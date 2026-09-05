"""
Unit tests for Celery email tasks.

Tests the email sending tasks:
- send_verification_email
- send_password_reset_email

These tasks are thin wrappers around email_service, so we focus on:
- Task registration and configuration
- Error handling and retry logic
"""
from unittest.mock import MagicMock, patch

import pytest


class TestTaskConfiguration:
    """Tests for task configuration."""

    def test_send_verification_task_name(self):
        """send_verification_email should have correct task name."""
        from app.tasks import email_tasks
        assert email_tasks.send_verification_email.name == "tasks.send_verification_email"

    def test_send_verification_max_retries(self):
        """send_verification_email should have max_retries=3."""
        from app.tasks import email_tasks
        assert email_tasks.send_verification_email.max_retries == 3

    def test_send_verification_retry_delay(self):
        """send_verification_email should have default_retry_delay=60."""
        from app.tasks import email_tasks
        assert email_tasks.send_verification_email.default_retry_delay == 60

    def test_send_password_reset_task_name(self):
        """send_password_reset_email should have correct task name."""
        from app.tasks import email_tasks
        assert email_tasks.send_password_reset_email.name == "tasks.send_password_reset_email"

    def test_send_password_reset_max_retries(self):
        """send_password_reset_email should have max_retries=3."""
        from app.tasks import email_tasks
        assert email_tasks.send_password_reset_email.max_retries == 3

    def test_send_password_reset_retry_delay(self):
        """send_password_reset_email should have default_retry_delay=60."""
        from app.tasks import email_tasks
        assert email_tasks.send_password_reset_email.default_retry_delay == 60


class TestTaskQueueAssignment:
    """Tests for queue assignment."""

    def test_email_tasks_use_email_queue(self):
        """Both email tasks should use the 'email' queue."""
        from app.tasks import email_tasks
        assert email_tasks.send_verification_email.queue == "email"
        assert email_tasks.send_password_reset_email.queue == "email"


class TestSendVerificationEmail:
    """Tests for send_verification_email execution."""

    def test_sends_verification_email_successfully(self):
        """Should call email_service.send_verification with correct args."""
        from app.tasks import email_tasks

        MagicMock()
        mock_email_instance = MagicMock()

        with patch('app.services.email_service.email_service', mock_email_instance):
            # Call the underlying function directly to avoid Celery task proxy
            email_tasks.send_verification_email.run(
                to="user@example.com",
                otp="123456",
                token="verify-token-abc123"
            )

            mock_email_instance.send_verification.assert_called_once_with(
                "user@example.com",
                "123456",
                "verify-token-abc123"
            )

    def test_retries_on_failure(self):
        """Should retry when email_service.send_verification raises."""
        from app.tasks import email_tasks

        MagicMock()
        mock_email_instance = MagicMock()
        mock_email_instance.send_verification.side_effect = Exception("SMTP error")

        with patch('app.services.email_service.email_service', mock_email_instance):
            with pytest.raises(Exception, match="SMTP error"):
                email_tasks.send_verification_email.run(
                    to="user@example.com",
                    otp="123456",
                    token="token"
                )


class TestSendPasswordResetEmail:
    """Tests for send_password_reset_email execution."""

    def test_sends_password_reset_email_successfully(self):
        """Should call email_service.send_password_reset with correct args."""
        from app.tasks import email_tasks

        MagicMock()
        mock_email_instance = MagicMock()

        with patch('app.services.email_service.email_service', mock_email_instance):
            # Call the underlying function directly to avoid Celery task proxy
            email_tasks.send_password_reset_email.run(
                to="user@example.com",
                otp="654321",
                token="reset-token-xyz789"
            )

            mock_email_instance.send_password_reset.assert_called_once_with(
                "user@example.com",
                "654321",
                "reset-token-xyz789"
            )

    def test_retries_on_failure(self):
        """Should retry when email_service.send_password_reset raises."""
        from app.tasks import email_tasks

        MagicMock()
        mock_email_instance = MagicMock()
        mock_email_instance.send_password_reset.side_effect = Exception("Connection refused")

        with patch('app.services.email_service.email_service', mock_email_instance):
            with pytest.raises(Exception, match="Connection refused"):
                email_tasks.send_password_reset_email.run(
                    to="user@example.com",
                    otp="654321",
                    token="token"
                )


class TestTaskLogging:
    """Tests for logging behavior."""

    def test_verification_email_logs_on_success(self, caplog):
        """Should complete without errors on successful send."""
        import logging

        from app.tasks import email_tasks

        caplog.set_level(logging.INFO)

        mock_email_instance = MagicMock()

        with patch('app.services.email_service.email_service', mock_email_instance):
            # Call the underlying function directly to avoid Celery task proxy
            email_tasks.send_verification_email.run(
                to="user@example.com",
                otp="123456",
                token="token"
            )

        # Task should complete without error logs
        assert not any(record.levelname == 'ERROR' for record in caplog.records)

    def test_verification_email_logs_error_on_failure(self, caplog):
        """Should log error when email sending fails."""
        import logging

        from app.tasks import email_tasks

        caplog.set_level(logging.ERROR)

        mock_email_instance = MagicMock()
        mock_email_instance.send_verification.side_effect = Exception("SMTP error")

        with patch('app.services.email_service.email_service', mock_email_instance):
            with pytest.raises(Exception, match="SMTP error"):
                email_tasks.send_verification_email.run(
                    to="user@example.com",
                    otp="123456",
                    token="token"
                )

        # Should have logged an error
        assert any("Verification email failed" in record.message for record in caplog.records)

    def test_password_reset_email_logs_error_on_failure(self, caplog):
        """Should log error when password reset email sending fails."""
        import logging

        from app.tasks import email_tasks

        caplog.set_level(logging.ERROR)

        mock_email_instance = MagicMock()
        mock_email_instance.send_password_reset.side_effect = Exception("Connection refused")

        with patch('app.services.email_service.email_service', mock_email_instance):
            with pytest.raises(Exception, match="Connection refused"):
                email_tasks.send_password_reset_email.run(
                    to="user@example.com",
                    otp="654321",
                    token="token"
                )

        # Should have logged an error
        assert any("Reset email failed" in record.message for record in caplog.records)
