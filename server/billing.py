"""Stripe billing: Checkout sessions for subscriptions and webhook handling
that grants monthly credits. Price->plan/credits mapping comes from the
STRIPE_PRICES env (JSON), so you never hard-code price ids."""
import json

import stripe
from sqlmodel import select

from .config import settings
from .db import CreditLedger, User, get_session, _now

stripe.api_key = settings.STRIPE_SECRET_KEY


def _price_map() -> dict:
    try:
        return json.loads(settings.STRIPE_PRICES or "{}")
    except json.JSONDecodeError:
        return {}


def create_checkout(user: User, price_id: str) -> str:
    """Create a subscription Checkout session, return its URL. Reuses/creates a
    Stripe customer tied to the user so webhooks can map back."""
    customer_id = user.stripe_customer_id
    if not customer_id:
        cust = stripe.Customer.create(email=user.email, metadata={"user_id": user.id})
        customer_id = cust["id"]
        with get_session() as s:
            u = s.get(User, user.id)
            u.stripe_customer_id = customer_id
            s.add(u); s.commit()
    session = stripe.checkout.Session.create(
        mode="subscription",
        customer=customer_id,
        line_items=[{"price": price_id, "quantity": 1}],
        client_reference_id=user.id,
        success_url=settings.STRIPE_SUCCESS_URL,
        cancel_url=settings.STRIPE_CANCEL_URL,
    )
    return session["url"]


def _grant(user_id: str, plan: str, credits: int, reason: str) -> None:
    with get_session() as s:
        user = s.get(User, user_id)
        if not user:
            return
        user.plan = plan
        user.credits += credits
        s.add(user)
        s.add(CreditLedger(user_id=user_id, delta=credits, reason=reason))
        s.commit()


def _user_for_customer(customer_id: str):
    with get_session() as s:
        return s.exec(select(User).where(User.stripe_customer_id == customer_id)).first()


def handle_webhook(payload: bytes, sig_header: str) -> dict:
    """Verify and process a Stripe webhook. Grants credits on successful
    payment; downgrades to free when a subscription ends."""
    event = stripe.Webhook.construct_event(
        payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    etype = event["type"]
    obj = event["data"]["object"]
    prices = _price_map()

    if etype in ("checkout.session.completed", "invoice.paid"):
        customer_id = obj.get("customer")
        user = _user_for_customer(customer_id)
        if not user and obj.get("client_reference_id"):
            with get_session() as s:
                user = s.get(User, obj["client_reference_id"])
        if user:
            # find the purchased price id and map to plan/credits
            price_id = _extract_price_id(obj)
            spec = prices.get(price_id or "", {})
            _grant(user.id, spec.get("plan", "creator"),
                   int(spec.get("credits", 0)), f"{etype} {price_id}")
        return {"handled": etype}

    if etype == "customer.subscription.deleted":
        user = _user_for_customer(obj.get("customer"))
        if user:
            with get_session() as s:
                u = s.get(User, user.id)
                u.plan = "free"
                s.add(u); s.commit()
        return {"handled": etype}

    return {"ignored": etype}


def _extract_price_id(obj: dict):
    """Pull a price id out of a checkout session or invoice object."""
    # invoice
    try:
        lines = obj.get("lines", {}).get("data", [])
        if lines:
            return lines[0]["price"]["id"]
    except Exception:
        pass
    # checkout session: need to look up line items
    try:
        if obj.get("id", "").startswith("cs_"):
            items = stripe.checkout.Session.list_line_items(obj["id"], limit=1)
            return items["data"][0]["price"]["id"]
    except Exception:
        pass
    return None
