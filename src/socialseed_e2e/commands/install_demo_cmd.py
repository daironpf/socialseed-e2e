"""Install demo command for socialseed-e2e CLI.

This module provides the install-demo command using POO and SOLID principles.
"""

from pathlib import Path

import click
from rich.console import Console

from socialseed_e2e.utils import TemplateEngine


console = Console()


class DemoInstaller:
    """Handles installation of demo services (Single Responsibility)."""

    DEMO_SERVICES = [
        ("rest", "api-rest-demo.py", "demo_api_page.py"),
        ("grpc", "api-grpc-demo.py", None),
        ("websocket", "api-websocket-demo.py", None),
        ("auth", "api-auth-demo.py", None),
        ("ecommerce", "api-ecommerce-demo.py", "ecommerce_service_page.py"),
        ("chat", "api-chat-demo.py", "chat_service_page.py"),
        ("booking", "api-booking-demo.py", "booking_service_page.py"),
        ("notifications", "api_notifications_demo.py", "notifications_service_page.py"),
        ("filestorage", "api_filestorage_demo.py", "filestorage_service_page.py"),
        ("social", "api_social_demo.py", "social_service_page.py"),
        ("payments", "api_payments_demo.py", "payments_service_page.py"),
        ("analytics", "api_analytics_demo.py", "analytics_service_page.py"),
        ("ml", "api_ml_demo.py", "ml_service_page.py"),
        ("iot", "api_iot_demo.py", "iot_service_page.py"),
        ("saas", "api_saas_demo.py", "saas_service_page.py"),
        ("workflows", "api_workflows_demo.py", "workflows_service_page.py"),
    ]

    def __init__(self, force: bool = False):
        self.force = force
        self.engine = TemplateEngine()

    def install(self) -> None:
        """Install all demo services."""
        target_path = Path.cwd()

        console.print(
            f"\n🎯 [bold green]Installing demo services to:[/bold green] {target_path}\n"
        )

        self._create_demo_directories(target_path)
        self._create_demo_apis(target_path)
        self._create_demo_service(target_path)
        self._update_e2e_conf()

    def _create_demo_directories(self, target_path: Path) -> None:
        """Create demo directory structure."""
        demos_path = target_path / "demos"

        for demo_type, _, _ in self.DEMO_SERVICES:
            demo_path = demos_path / demo_type
            demo_path.mkdir(parents=True, exist_ok=True)

    def _create_demo_apis(self, target_path: Path) -> None:
        """Create demo API files."""
        demos_path = target_path / "demos"

        for demo_type, api_file, _ in self.DEMO_SERVICES:
            demo_api_path = demos_path / demo_type / api_file

            if not demo_api_path.exists() or self.force:
                self.engine.render_to_file(
                    f"api_{demo_type}_demo.py.template",
                    {},
                    str(demo_api_path),
                    overwrite=self.force,
                )
                console.print(
                    f"  [green]✓[/green] Created: demos/{demo_type}/{api_file}"
                )

    def _create_demo_service(self, target_path: Path) -> None:
        """Create demo service files."""
        demo_service_path = target_path / "services" / "demo-api"
        demo_modules_path = demo_service_path / "modules"

        if not demo_service_path.exists() or self.force:
            demo_service_path.mkdir(parents=True, exist_ok=True)
            demo_modules_path.mkdir(exist_ok=True)

            # Create __init__ files
            (demo_service_path / "__init__.py").write_text("")
            (demo_modules_path / "__init__.py").write_text("")

            # Create service page
            self.engine.render_to_file(
                "demo_service_page.py.template",
                {},
                str(demo_service_path / "demo_api_page.py"),
                overwrite=self.force,
            )
            console.print(
                "  [green]✓[/green] Created: services/demo-api/demo_api_page.py"
            )

            # Create data schema
            self.engine.render_to_file(
                "demo_data_schema.py.template",
                {},
                str(demo_service_path / "data_schema.py"),
                overwrite=self.force,
            )
            console.print(
                "  [green]✓[/green] Created: services/demo-api/data_schema.py"
            )

            # Create config
            self.engine.render_to_file(
                "demo_config.py.template",
                {},
                str(demo_service_path / "config.py"),
                overwrite=self.force,
            )
            console.print("  [green]✓[/green] Created: services/demo-api/config.py")

            # Create test module
            self.engine.render_to_file(
                "demo_test_health.py.template",
                {},
                str(demo_modules_path / "01_health_check.py"),
                overwrite=self.force,
            )
            console.print(
                "  [green]✓[/green] Created: services/demo-api/modules/01_health_check.py"
            )

        # Create ecommerce demo service
        self._create_ecommerce_service(target_path)

    def _create_ecommerce_service(self, target_path: Path) -> None:
        """Create e-commerce demo service files."""
        ecommerce_service_path = target_path / "services" / "ecommerce-demo"
        ecommerce_modules_path = ecommerce_service_path / "modules"

        if not ecommerce_service_path.exists() or self.force:
            ecommerce_service_path.mkdir(parents=True, exist_ok=True)
            ecommerce_modules_path.mkdir(exist_ok=True)

            # Create __init__ files
            (ecommerce_service_path / "__init__.py").write_text("")
            (ecommerce_modules_path / "__init__.py").write_text("")

            # Create service page
            self.engine.render_to_file(
                "ecommerce_service_page.py.template",
                {},
                str(ecommerce_service_path / "ecommerce_page.py"),
                overwrite=self.force,
            )
            console.print(
                "  [green]✓[/green] Created: services/ecommerce-demo/ecommerce_page.py"
            )

            # Create data schema
            self.engine.render_to_file(
                "ecommerce_data_schema.py.template",
                {},
                str(ecommerce_service_path / "data_schema.py"),
                overwrite=self.force,
            )
            console.print(
                "  [green]✓[/green] Created: services/ecommerce-demo/data_schema.py"
            )

            # Create config
            self.engine.render_to_file(
                "ecommerce_config.py.template",
                {},
                str(ecommerce_service_path / "config.py"),
                overwrite=self.force,
            )
            console.print(
                "  [green]✓[/green] Created: services/ecommerce-demo/config.py"
            )

            # Create test modules
            test_files = [
                ("01_list_products", "ecommerce_test_01_list_products.py.template"),
                ("02_filter_products", "ecommerce_test_02_filter_products.py.template"),
                ("03_get_product", "ecommerce_test_03_get_product.py.template"),
                ("04_add_to_cart", "ecommerce_test_04_add_to_cart.py.template"),
                ("05_update_cart", "ecommerce_test_05_update_cart.py.template"),
                ("06_checkout", "ecommerce_test_06_checkout.py.template"),
                (
                    "07_concurrent_inventory",
                    "ecommerce_test_07_concurrent_inventory.py.template",
                ),
                ("08_payment", "ecommerce_test_08_payment.py.template"),
                ("09_order_status", "ecommerce_test_09_order_status.py.template"),
                ("10_webhook_retry", "ecommerce_test_10_webhook_retry.py.template"),
            ]

            for prefix, template in test_files:
                self.engine.render_to_file(
                    template,
                    {},
                    str(ecommerce_modules_path / f"{prefix}.py"),
                    overwrite=self.force,
                )
                console.print(
                    f"  [green]✓[/green] Created: services/ecommerce-demo/modules/{prefix}.py"
                )

        # Create chat demo service
        self._create_chat_service(target_path)

    def _create_chat_service(self, target_path: Path) -> None:
        """Create chat demo service files."""
        chat_service_path = target_path / "services" / "chat-demo"
        chat_modules_path = chat_service_path / "modules"

        if not chat_service_path.exists() or self.force:
            chat_service_path.mkdir(parents=True, exist_ok=True)
            chat_modules_path.mkdir(exist_ok=True)

            (chat_service_path / "__init__.py").write_text("")
            (chat_modules_path / "__init__.py").write_text("")

            self.engine.render_to_file(
                "chat_service_page.py.template",
                {},
                str(chat_service_path / "chat_page.py"),
                overwrite=self.force,
            )
            console.print("  [green]✓[/green] Created: services/chat-demo/chat_page.py")

            self.engine.render_to_file(
                "chat_data_schema.py.template",
                {},
                str(chat_service_path / "data_schema.py"),
                overwrite=self.force,
            )
            console.print(
                "  [green]✓[/green] Created: services/chat-demo/data_schema.py"
            )

            self.engine.render_to_file(
                "chat_config.py.template",
                {},
                str(chat_service_path / "config.py"),
                overwrite=self.force,
            )
            console.print("  [green]✓[/green] Created: services/chat-demo/config.py")

            test_files = [
                ("01_auth", "chat_test_01_auth.py.template"),
                ("02_list_users", "chat_test_02_list_users.py.template"),
                ("03_presence", "chat_test_03_presence.py.template"),
                ("04_rooms", "chat_test_04_rooms.py.template"),
                ("05_messages", "chat_test_05_messages.py.template"),
                ("06_membership", "chat_test_06_membership.py.template"),
                ("07_typing", "chat_test_07_typing.py.template"),
                ("08_reactions", "chat_test_08_reactions.py.template"),
                ("09_threads", "chat_test_09_threads.py.template"),
                ("10_chat_workflow", "chat_test_10_chat_workflow.py.template"),
            ]

            for prefix, template in test_files:
                self.engine.render_to_file(
                    template,
                    {},
                    str(chat_modules_path / f"{prefix}.py"),
                    overwrite=self.force,
                )
                console.print(
                    f"  [green]✓[/green] Created: services/chat-demo/modules/{prefix}.py"
                )

        # Create booking demo service
        self._create_booking_service(target_path)

    def _create_booking_service(self, target_path: Path) -> None:
        """Create booking demo service files."""
        booking_service_path = target_path / "services" / "booking-demo"
        booking_modules_path = booking_service_path / "modules"

        if not booking_service_path.exists() or self.force:
            booking_service_path.mkdir(parents=True, exist_ok=True)
            booking_modules_path.mkdir(exist_ok=True)

            (booking_service_path / "__init__.py").write_text("")
            (booking_modules_path / "__init__.py").write_text("")

            self.engine.render_to_file(
                "booking_service_page.py.template",
                {},
                str(booking_service_path / "booking_page.py"),
                overwrite=self.force,
            )
            console.print(
                "  [green]✓[/green] Created: services/booking-demo/booking_page.py"
            )

            self.engine.render_to_file(
                "booking_data_schema.py.template",
                {},
                str(booking_service_path / "data_schema.py"),
                overwrite=self.force,
            )
            console.print(
                "  [green]✓[/green] Created: services/booking-demo/data_schema.py"
            )

            self.engine.render_to_file(
                "booking_config.py.template",
                {},
                str(booking_service_path / "config.py"),
                overwrite=self.force,
            )
            console.print("  [green]✓[/green] Created: services/booking-demo/config.py")

            test_files = [
                ("01_list_services", "booking_test_01_list_services.py.template"),
                ("02_get_service", "booking_test_02_get_service.py.template"),
                ("03_availability", "booking_test_03_availability.py.template"),
                (
                    "04_create_appointment",
                    "booking_test_04_create_appointment.py.template",
                ),
                (
                    "05_list_appointments",
                    "booking_test_05_list_appointments.py.template",
                ),
                (
                    "06_cancel_appointment",
                    "booking_test_06_cancel_appointment.py.template",
                ),
                ("07_reschedule", "booking_test_07_reschedule.py.template"),
                ("08_waitlist", "booking_test_08_waitlist.py.template"),
                ("09_double_booking", "booking_test_09_double_booking.py.template"),
                ("10_booking_workflow", "booking_test_10_booking_workflow.py.template"),
            ]

            for prefix, template in test_files:
                self.engine.render_to_file(
                    template,
                    {},
                    str(booking_modules_path / f"{prefix}.py"),
                    overwrite=self.force,
                )
                console.print(
                    f"  [green]✓[/green] Created: services/booking-demo/modules/{prefix}.py"
                )

        # Create notifications demo service
        self._create_notifications_service(target_path)

        # Create filestorage demo service
        self._create_filestorage_service(target_path)

        # Create social demo service
        self._create_social_service(target_path)

        # Create payments demo service
        self._create_payments_service(target_path)

    def _create_notifications_service(self, target_path: Path) -> None:
        """Create notifications demo service files."""
        notif_service_path = target_path / "services" / "notifications-demo"
        notif_modules_path = notif_service_path / "modules"

        if not notif_service_path.exists() or self.force:
            notif_service_path.mkdir(parents=True, exist_ok=True)
            notif_modules_path.mkdir(exist_ok=True)

            (notif_service_path / "__init__.py").write_text("")
            (notif_modules_path / "__init__.py").write_text("")

            self.engine.render_to_file(
                "notifications_service_page.py.template",
                {},
                str(notif_service_path / "notifications_page.py"),
                overwrite=self.force,
            )
            console.print(
                "  [green]✓[/green] Created: services/notifications-demo/notifications_page.py"
            )

            self.engine.render_to_file(
                "notifications_data_schema.py.template",
                {},
                str(notif_service_path / "data_schema.py"),
                overwrite=self.force,
            )
            console.print(
                "  [green]✓[/green] Created: services/notifications-demo/data_schema.py"
            )

            self.engine.render_to_file(
                "notifications_config.py.template",
                {},
                str(notif_service_path / "config.py"),
                overwrite=self.force,
            )
            console.print(
                "  [green]✓[/green] Created: services/notifications-demo/config.py"
            )

            test_files = [
                (
                    "01_send_notification",
                    "notifications_test_01_send_notification.py.template",
                ),
                (
                    "02_list_notifications",
                    "notifications_test_02_list_notifications.py.template",
                ),
                (
                    "03_get_notification",
                    "notifications_test_03_get_notification.py.template",
                ),
                ("04_channels", "notifications_test_04_channels.py.template"),
                ("05_templates", "notifications_test_05_templates.py.template"),
                ("06_webhooks", "notifications_test_06_webhooks.py.template"),
                (
                    "07_delete_webhook",
                    "notifications_test_07_delete_webhook.py.template",
                ),
                ("08_multi_channel", "notifications_test_08_multi_channel.py.template"),
                ("09_statuses", "notifications_test_09_statuses.py.template"),
                (
                    "10_notifications_workflow",
                    "notifications_test_10_notifications_workflow.py.template",
                ),
            ]

            for prefix, template in test_files:
                self.engine.render_to_file(
                    template,
                    {},
                    str(notif_modules_path / f"{prefix}.py"),
                    overwrite=self.force,
                )
                console.print(
                    f"  [green]✓[/green] Created: services/notifications-demo/modules/{prefix}.py"
                )

    def _update_e2e_conf(self) -> None:
        """Update e2e.conf with demo service."""
        from socialseed_e2e.core.config_loader import ApiConfigLoader, ServiceConfig

        try:
            loader = ApiConfigLoader()
            config = loader.load()

            if config.services is None:
                config.services = {}

            config.services["demo-api"] = ServiceConfig(
                name="demo-api",
                base_url="http://localhost:8765",
                health_endpoint="/health",
            )

            config.services["ecommerce-demo"] = ServiceConfig(
                name="ecommerce-demo",
                base_url="http://localhost:5004",
                health_endpoint="/health",
            )

            config.services["chat-demo"] = ServiceConfig(
                name="chat-demo",
                base_url="http://localhost:5005",
                health_endpoint="/health",
            )

            config.services["booking-demo"] = ServiceConfig(
                name="booking-demo",
                base_url="http://localhost:5006",
                health_endpoint="/health",
            )

            config.services["notifications-demo"] = ServiceConfig(
                name="notifications-demo",
                base_url="http://localhost:5007",
                health_endpoint="/health",
            )

            loader.save(config)
            console.print("  [green]✓[/green] Updated: e2e.conf")
        except Exception as e:
            console.print(f"  [yellow]⚠[/yellow] Could not update e2e.conf: {e}")

    def _create_filestorage_service(self, target_path: Path) -> None:
        """Create filestorage demo service files."""
        fs_service_path = target_path / "services" / "filestorage-demo"
        fs_modules_path = fs_service_path / "modules"

        if not fs_service_path.exists() or self.force:
            fs_service_path.mkdir(parents=True, exist_ok=True)
            fs_modules_path.mkdir(exist_ok=True)

            (fs_service_path / "__init__.py").write_text("")
            (fs_modules_path / "__init__.py").write_text("")

            self.engine.render_to_file(
                "filestorage_service_page.py.template",
                {},
                str(fs_service_path / "filestorage_page.py"),
                overwrite=self.force,
            )
            console.print(
                "  [green]✓[/green] Created: services/filestorage-demo/filestorage_page.py"
            )

            self.engine.render_to_file(
                "filestorage_data_schema.py.template",
                {},
                str(fs_service_path / "data_schema.py"),
                overwrite=self.force,
            )
            console.print(
                "  [green]✓[/green] Created: services/filestorage-demo/data_schema.py"
            )

            self.engine.render_to_file(
                "filestorage_config.py.template",
                {},
                str(fs_service_path / "config.py"),
                overwrite=self.force,
            )
            console.print(
                "  [green]✓[/green] Created: services/filestorage-demo/config.py"
            )

            for prefix in [
                ("01_create_bucket", "filestorage_test_01_create_bucket.py.template"),
                ("02_simple_upload", "filestorage_test_02_simple_upload.py.template"),
                (
                    "03_multipart_upload",
                    "filestorage_test_03_multipart_upload.py.template",
                ),
                ("04_download", "filestorage_test_04_download.py.template"),
                ("05_presigned_url", "filestorage_test_05_presigned_url.py.template"),
                ("06_delete_object", "filestorage_test_06_delete_object.py.template"),
            ]:
                self.engine.render_to_file(
                    prefix[1],
                    {},
                    str(fs_modules_path / f"{prefix[0]}.py"),
                    overwrite=self.force,
                )
                console.print(
                    f"  [green]✓[/green] Created: services/filestorage-demo/modules/{prefix[0]}.py"
                )

    def _create_social_service(self, target_path: Path) -> None:
        """Create social demo service files."""
        social_service_path = target_path / "services" / "social-demo"
        social_modules_path = social_service_path / "modules"

        if not social_service_path.exists() or self.force:
            social_service_path.mkdir(parents=True, exist_ok=True)
            social_modules_path.mkdir(exist_ok=True)

            (social_service_path / "__init__.py").write_text("")
            (social_modules_path / "__init__.py").write_text("")

            self.engine.render_to_file(
                "social_service_page.py.template",
                {},
                str(social_service_path / "social_page.py"),
                overwrite=self.force,
            )
            console.print(
                "  [green]✓[/green] Created: services/social-demo/social_page.py"
            )

            self.engine.render_to_file(
                "social_data_schema.py.template",
                {},
                str(social_service_path / "data_schema.py"),
                overwrite=self.force,
            )
            console.print(
                "  [green]✓[/green] Created: services/social-demo/data_schema.py"
            )

            self.engine.render_to_file(
                "social_config.py.template",
                {},
                str(social_service_path / "config.py"),
                overwrite=self.force,
            )
            console.print("  [green]✓[/green] Created: services/social-demo/config.py")

            for prefix in [
                ("01_create_user", "social_test_01_create_user.py.template"),
                ("02_follow", "social_test_02_follow.py.template"),
                ("03_create_post", "social_test_03_create_post.py.template"),
                ("04_like_post", "social_test_04_like_post.py.template"),
                ("05_comment", "social_test_05_comment.py.template"),
                ("06_feed", "social_test_06_feed.py.template"),
            ]:
                self.engine.render_to_file(
                    prefix[1],
                    {},
                    str(social_modules_path / f"{prefix[0]}.py"),
                    overwrite=self.force,
                )
                console.print(
                    f"  [green]✓[/green] Created: services/social-demo/modules/{prefix[0]}.py"
                )

    def _create_payments_service(self, target_path: Path) -> None:
        """Create payments demo service files."""
        pay_service_path = target_path / "services" / "payments-demo"
        pay_modules_path = pay_service_path / "modules"

        if not pay_service_path.exists() or self.force:
            pay_service_path.mkdir(parents=True, exist_ok=True)
            pay_modules_path.mkdir(exist_ok=True)

            (pay_service_path / "__init__.py").write_text("")
            (pay_modules_path / "__init__.py").write_text("")

            self.engine.render_to_file(
                "payments_service_page.py.template",
                {},
                str(pay_service_path / "payments_page.py"),
                overwrite=self.force,
            )
            console.print(
                "  [green]✓[/green] Created: services/payments-demo/payments_page.py"
            )

            self.engine.render_to_file(
                "payments_data_schema.py.template",
                {},
                str(pay_service_path / "data_schema.py"),
                overwrite=self.force,
            )
            console.print(
                "  [green]✓[/green] Created: services/payments-demo/data_schema.py"
            )

            self.engine.render_to_file(
                "payments_config.py.template",
                {},
                str(pay_service_path / "config.py"),
                overwrite=self.force,
            )
            console.print(
                "  [green]✓[/green] Created: services/payments-demo/config.py"
            )

            for prefix in [
                ("01_create_intent", "payments_test_01_create_intent.py.template"),
                ("02_confirm", "payments_test_02_confirm.py.template"),
                ("03_methods", "payments_test_03_methods.py.template"),
                ("04_refund", "payments_test_04_refund.py.template"),
                ("05_idempotency", "payments_test_05_idempotency.py.template"),
                ("06_list_charges", "payments_test_06_list_charges.py.template"),
            ]:
                self.engine.render_to_file(
                    prefix[1],
                    {},
                    str(pay_modules_path / f"{prefix[0]}.py"),
                    overwrite=self.force,
                )
                console.print(
                    f"  [green]✓[/green] Created: services/payments-demo/modules/{prefix[0]}.py"
                )


@click.command()
@click.option("--force", is_flag=True, help="Overwrite existing files")
def install_demo_cmd(force: bool):
    """Install demo APIs and example services to an existing project.

    This command adds multiple demo APIs covering different protocols:
    - REST API (basic CRUD) on port 5000
    - gRPC API (with proto definitions) on port 50051
    - WebSocket API (real-time) on port 50052
    - Auth API (JWT Bearer tokens) on port 5003

    Each demo includes a runnable server and corresponding test services.

    Example:
        e2e init my-project
        cd my-project
        e2e install-demo
    """
    installer = DemoInstaller(force=force)
    installer.install()

    console.print(
        "\n[bold green]✅ Demo services installed successfully![/bold green]\n"
    )
    console.print("[bold]Next steps:[/bold]")
    console.print("  1. Run demo API: [cyan]python demos/rest/api-rest-demo.py[/cyan]")
    console.print("  2. Run tests: [cyan]e2e run --service demo-api[/cyan]")


def get_install_demo_command():
    """Get the install-demo command for lazy loading."""
    return install_demo_cmd


__all__ = ["install_demo_cmd", "get_install_demo_command"]
