from unittest import TestCase
from unittest.mock import patch

from runrestic.restic import installer


class TestInstaller(TestCase):
    def test_restic_check_is_installed(self):
        # Mock the `which` function to simulate restic being installed
        with patch("runrestic.restic.installer.which", return_value="/usr/local/bin/restic"):
            self.assertTrue(installer.restic_check())

    def test_restic_check_do_install(self):
        # Mock the `input` function to simulate user input for installation
        with (
            patch("runrestic.restic.installer.which", return_value=None),
            patch("runrestic.restic.installer.download_restic"),
        ):
            with patch("builtins.input", return_value="y"):
                self.assertTrue(installer.restic_check())
            with patch("builtins.input", return_value="n"):
                self.assertFalse(installer.restic_check())

    def test_download_restic(self):
        # Mock the requests.get method to simulate a successful response
        with patch("runrestic.restic.installer.requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.content = b'{"assets": [{"name": "restic_linux_amd64.bz2", "browser_download_url": "https://example.com/restic_linux_amd64.bz2"}]}'
            with (
                patch("runrestic.restic.installer.bz2.decompress", return_value=b"dummy_program"),
                patch("runrestic.restic.installer.Path.write_bytes"),
                patch("runrestic.restic.installer.Path.chmod"),
            ):
                installer.download_restic()
                mock_get.assert_any_call("https://api.github.com/repos/restic/restic/releases/latest", timeout=10)
                mock_get.assert_called_with(
                    "https://example.com/restic_linux_amd64.bz2", allow_redirects=True, timeout=60
                )

    def test_download_restic_permission_error(self):
        # Mock the requests.get method to simulate a successful response
        with (
            patch("runrestic.restic.installer.requests.get") as mock_get,
            patch("runrestic.restic.installer.bz2.decompress", return_value=b"dummy_program"),
            patch("runrestic.restic.installer.Path.chmod"),
        ):
            mock_get.return_value.status_code = 200
            mock_get.return_value.content = b'{"assets": [{"name": "restic_linux_amd64.bz2", "browser_download_url": "https://example.com/restic_linux_amd64.bz2"}]}'
            with (
                patch("builtins.print") as mock_print,
                patch("runrestic.restic.installer.Path.write_bytes", side_effect=PermissionError) as mock_write,
                patch("builtins.input", return_value=""),
            ):
                installer.download_restic()
                mock_print.assert_any_call("\nTry re-running this as root.")
                mock_write.assert_called_once()

    def test_download_restic_permission_error_alt(self):
        # Mock the requests.get method to simulate a successful response
        with (
            patch("runrestic.restic.installer.requests.get") as mock_get,
            patch("runrestic.restic.installer.bz2.decompress", return_value=b"dummy_program"),
            patch("runrestic.restic.installer.Path.chmod"),
        ):
            mock_get.return_value.status_code = 200
            mock_get.return_value.content = b'{"assets": [{"name": "restic_linux_amd64.bz2", "browser_download_url": "https://example.com/restic_linux_amd64.bz2"}]}'
            with (
                patch("builtins.print") as mock_print,
                patch("runrestic.restic.installer.Path.write_bytes", side_effect=[PermissionError, None]) as mock_write,
                patch("builtins.input", return_value="alt_path"),
            ):
                installer.download_restic()
                mock_print.assert_any_call("\nTry re-running this as root.")
                self.assertEqual(mock_write.call_count, 2)

    def test_download_restic_no_assets(self):
        # Mock the requests.get method to simulate a successful response
        with patch("runrestic.restic.installer.requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.content = b'{"dummy": 42}'
            with patch("builtins.print") as mock_print:
                installer.download_restic()
                mock_print.assert_called_with("Error: Could not find a suitable Restic binary to download.")
                mock_get.assert_called_with("https://api.github.com/repos/restic/restic/releases/latest", timeout=10)

    def test_download_restic_assets_no_match(self):
        # Mock the requests.get method to simulate a successful response
        with patch("runrestic.restic.installer.requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.content = b'{"assets": [{"name": "restic_fake_os.bz2", "browser_download_url": "https://example.com/restic_fake_os.bz2"}]}'
            with patch("builtins.print") as mock_print:
                installer.download_restic()
                mock_print.assert_called_with("Error: Could not find a suitable Restic binary to download.")
                mock_get.assert_called_with("https://api.github.com/repos/restic/restic/releases/latest", timeout=10)

    def test_download_restic_timeout_fetch_release(self):
        # Mock the requests.get method to simulate a timeout
        with (
            patch("runrestic.restic.installer.requests.get", side_effect=installer.requests.exceptions.Timeout),
            patch("builtins.print") as mock_print,
        ):
            installer.download_restic()
            mock_print.assert_called_with("Error: Unable to fetch the latest Restic release due to a timeout.")

    def test_download_restic_request_exception_fetch_release(self):
        # Mock the requests.get method to simulate a request exception
        with (
            patch(
                "runrestic.restic.installer.requests.get",
                side_effect=installer.requests.exceptions.RequestException("Request failed"),
            ),
            patch("builtins.print") as mock_print,
        ):
            installer.download_restic()
            mock_print.assert_called_with("Error: Unable to fetch the latest Restic release: Request failed")

    def test_download_restic_timeout_download_program(self):
        # Mock the requests.get method to simulate a timeout during program download
        with (
            patch(
                "runrestic.restic.installer.requests.get",
                side_effect=[
                    # Simulate successful response for fetching release
                    type(
                        "Response",
                        (object,),
                        {
                            "status_code": 200,
                            "content": b'{"assets": [{"name": "restic_linux_amd64.bz2", "browser_download_url": "https://example.com/restic_linux_amd64.bz2"}]}',
                            "raise_for_status": lambda x: True,
                        },
                    )(),
                    # Simulate timeout during program download
                    installer.requests.exceptions.Timeout,
                ],
            ),
            patch("builtins.print") as mock_print,
        ):
            installer.download_restic()
            mock_print.assert_called_with("Error: Unable to download the Restic binary due to a timeout.")

    def test_download_restic_request_exception_download_program(self):
        # Mock the requests.get method to simulate a request exception
        with (
            patch(
                "runrestic.restic.installer.requests.get",
                side_effect=[
                    # Simulate successful response for fetching release
                    type(
                        "Response",
                        (object,),
                        {
                            "status_code": 200,
                            "content": b'{"assets": [{"name": "restic_linux_amd64.bz2", "browser_download_url": "https://example.com/restic_linux_amd64.bz2"}]}',
                            "raise_for_status": lambda x: True,
                        },
                    )(),
                    # Simulate exception during program download
                    installer.requests.exceptions.RequestException("Request failed"),
                ],
            ),
            patch("builtins.print") as mock_print,
        ):
            installer.download_restic()
            mock_print.assert_called_with("Error: Unable to download the Restic binary: Request failed")
