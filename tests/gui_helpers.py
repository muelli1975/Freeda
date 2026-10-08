"""Pump the native UI while asynchronous discovery, cropping and export run."""
import time


def wait_for_job(app, timeout=40):
    deadline = time.monotonic() + timeout
    def poll():
        if not app._busy or time.monotonic() >= deadline:
            app.quit()
        else:
            app.after(20, poll)
    app.after(20, poll)
    app.mainloop()
    assert not app._busy, "Processing did not finish within the test deadline"
