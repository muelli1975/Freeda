"""Cancellation shared by discovery, rendering and atomic export."""
from threading import Event


class Cancelled(Exception):
    pass


def check_cancel(cancel: Event | None) -> None:
    if cancel is not None and cancel.is_set():
        raise Cancelled()
