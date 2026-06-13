"""Billing routes — Stripe Checkout, webhook, and subscription management."""

import os
import stripe
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from database import db, Business, Account, AccountMembership

billing_bp = Blueprint("billing", __name__)


def _stripe():
    stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
    return stripe


def _get_owner_membership(account_id):
    """Return membership only if current user is the owner, else 404."""
    return AccountMembership.query.filter_by(
        account_id=account_id,
        user_id=current_user.id,
        role="owner",
        revoked_at=None,
    ).first_or_404()


@billing_bp.route("/accounts/<account_id>/billing")
@login_required
def billing(account_id):
    """Show subscription status and management options to the account owner."""
    m = _get_owner_membership(account_id)
    account = m.account
    business = account.business
    return render_template("billing.html", account=account, business=business)


@billing_bp.route("/accounts/<account_id>/billing/checkout", methods=["POST"])
@login_required
def create_checkout(account_id):
    """Start a Stripe Checkout session for the $10/mo plan."""
    m = _get_owner_membership(account_id)
    account = m.account
    business = account.business

    s = _stripe()
    price_id = os.environ.get("STRIPE_PRICE_ID")
    if not price_id:
        flash("Billing is not configured yet. Please contact support.")
        return redirect(url_for("billing.billing", account_id=account_id))

    base_url = request.host_url.rstrip("/")
    session = s.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        customer_email=current_user.email,
        metadata={"business_id": business.id, "account_id": account_id},
        success_url=base_url + url_for("billing.checkout_success", account_id=account_id),
        cancel_url=base_url + url_for("billing.billing", account_id=account_id),
    )
    return redirect(session.url, code=303)


@billing_bp.route("/accounts/<account_id>/billing/success")
@login_required
def checkout_success(account_id):
    """Landing page after successful Stripe Checkout."""
    m = _get_owner_membership(account_id)
    business = m.account.business
    # Webhook will update the DB; show a holding page in the meantime
    flash("Payment successful! Your subscription is now active.")
    return redirect(url_for("billing.billing", account_id=account_id))


@billing_bp.route("/accounts/<account_id>/billing/portal", methods=["POST"])
@login_required
def customer_portal(account_id):
    """Redirect the owner to the Stripe Customer Portal to manage/cancel."""
    m = _get_owner_membership(account_id)
    business = m.account.business

    s = _stripe()
    if not business.stripe_customer_id:
        flash("No active subscription found.")
        return redirect(url_for("billing.billing", account_id=account_id))

    base_url = request.host_url.rstrip("/")
    portal = s.billing_portal.Session.create(
        customer=business.stripe_customer_id,
        return_url=base_url + url_for("billing.billing", account_id=account_id),
    )
    return redirect(portal.url, code=303)


@billing_bp.route("/webhook/stripe", methods=["POST"])
def stripe_webhook():
    """Handle Stripe webhook events to keep subscription_status in sync."""
    s = _stripe()
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    payload = request.get_data()
    sig = request.headers.get("Stripe-Signature", "")

    try:
        event = s.Webhook.construct_event(payload, sig, webhook_secret)
    except (ValueError, stripe.error.SignatureVerificationError):
        return {"error": "invalid payload"}, 400

    data = event["data"]["object"]

    if event["type"] == "checkout.session.completed":
        business_id = data.get("metadata", {}).get("business_id")
        customer_id = data.get("customer")
        business = Business.query.get(business_id)
        if business:
            business.stripe_customer_id = customer_id
            business.subscription_status = "active"
            db.session.commit()

    elif event["type"] in ("customer.subscription.updated", "customer.subscription.deleted"):
        customer_id = data.get("customer")
        business = Business.query.filter_by(stripe_customer_id=customer_id).first()
        if business:
            stripe_status = data.get("status", "cancelled")
            status_map = {
                "active":   "active",
                "trialing": "trialing",
                "past_due": "past_due",
                "canceled": "cancelled",
                "cancelled":"cancelled",
                "unpaid":   "past_due",
            }
            business.subscription_status = status_map.get(stripe_status, "cancelled")
            db.session.commit()

    return {"received": True}, 200
