"""Player to replay recorded sessions directly."""

import logging

from socialseed_e2e.core.base_page import BasePage
from socialseed_e2e.recorder.models import RecordedSession

logger = logging.getLogger(__name__)


class SessionPlayer:
    """Executes a RecordedSession using a BasePage instance."""

    @staticmethod
    def play(session: RecordedSession, page: BasePage):
        """Replay all interactions in the session."""
        logger.info(f"Replaying session: {session.name}")
        print(f"▶️ Replaying session: {session.name} ({len(session.interactions)} interactions)")

        for i, interaction in enumerate(session.interactions):
            print(f"  Step {i+1}: {interaction.method} {interaction.url}...", end="", flush=True)

            method_func = getattr(page, interaction.method.lower())

            kwargs = {}
            if interaction.request_body:
                if isinstance(interaction.request_body, dict):
                    kwargs["json"] = interaction.request_body
                else:
                    kwargs["data"] = interaction.request_body

            if interaction.request_headers:
                # Filter headers as in converter if needed
                kwargs["headers"] = interaction.request_headers

            try:
                response = method_func(interaction.url, **kwargs)
                page.assert_status(response, interaction.response_status)
                print(f" [green]OK[/green] ({response.status})")
            except Exception as e:
                print(" [red]FAILED[/red]")
                logger.error(f"Replay failed at step {i+1}: {e}")
                raise

        print(f"✅ Session '{session.name}' replayed successfully!")
