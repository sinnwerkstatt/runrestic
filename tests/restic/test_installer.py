from unittest import TestCase
from unittest.mock import patch, mock_open

from runrestic.restic import installer


class TestInstaller(TestCase):
    def test_restic_check_is_installed(self):
        # Mock the `which` function to simulate restic being installed
        with patch(
            "runrestic.restic.installer.which", return_value="/usr/local/bin/restic"
        ):
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
                patch(
                    "runrestic.restic.installer.bz2.decompress",
                    return_value=b"dummy_program",
                ),
                patch("runrestic.restic.installer.os.chmod") as mock_chmod,
                patch("builtins.open", new_callable=mock_open) as mock_file_open,
            ):
                installer.download_restic()
                mock_get.assert_any_call(
                    "https://api.github.com/repos/restic/restic/releases/latest",
                )
                mock_get.assert_called_with(
                    "https://example.com/restic_linux_amd64.bz2",
                    allow_redirects=True,
                )
                # Assert open() was called with the right path and mode
                mock_file_open.assert_called_once_with("/usr/local/bin/restic", "wb")
                mock_chmod.assert_called_once_with("/usr/local/bin/restic", 0o755)

    def test_download_restic_permission_error(self):
        # Mock the requests.get method to simulate a successful response
        with (
            patch("runrestic.restic.installer.requests.get") as mock_get,
            patch(
                "runrestic.restic.installer.bz2.decompress",
                return_value=b"dummy_program",
            ),
        ):
            mock_get.return_value.status_code = 200
            mock_get.return_value.content = b'{"assets": [{"name": "restic_linux_amd64.bz2", "browser_download_url": "https://example.com/restic_linux_amd64.bz2"}]}'
            with (
                patch("builtins.print") as mock_print,
                patch("builtins.open", new_callable=mock_open) as mock_file_open,
                patch("builtins.input", return_value=""),
            ):
                file_handle = mock_file_open()
                file_handle.write.side_effect = [
                    PermissionError,
                    None,
                ]
                installer.download_restic()
                mock_print.assert_any_call("\nTry re-running this as root.")
                file_handle.write.assert_called_once()

    def test_download_restic_permission_error_alt(self):
        # Mock the requests.get method to simulate a successful response
        with (
            patch("runrestic.restic.installer.requests.get") as mock_get,
            patch(
                "runrestic.restic.installer.bz2.decompress",
                return_value=b"dummy_program",
            ),
        ):
            mock_get.return_value.status_code = 200
            mock_get.return_value.content = b'{"assets": [{"name": "restic_linux_amd64.bz2", "browser_download_url": "https://example.com/restic_linux_amd64.bz2"}]}'
            with (
                patch("builtins.print") as mock_print,
                patch("builtins.open", new_callable=mock_open) as mock_file_open,
                patch(
                    "runrestic.restic.installer.os.chmod",
                ) as mock_chmod,
                patch("builtins.input", return_value="alt_path"),
            ):
                file_handle = mock_file_open()
                file_handle.write.side_effect = [
                    PermissionError,
                    None,
                ]
                installer.download_restic()
                mock_print.assert_any_call("\nTry re-running this as root.")
                self.assertEqual(file_handle.write.call_count, 2)
                mock_chmod.assert_called_once_with("alt_path", 0o755)

    def test_download_restic_no_assets(self):
        # Mock the requests.get method to simulate a successful response
        with patch("runrestic.restic.installer.requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.content = b'{"dummy": 42}'
            self.assertRaises(
                KeyError,
                installer.download_restic,
            )

    def test_download_restic_assets_no_match(self):
        # Mock the requests.get method to simulate a successful response
        with patch("runrestic.restic.installer.requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.content = b'{"assets": [{"name": "restic_fake_os.bz2", "browser_download_url": "https://example.com/restic_fake_os.bz2"}]}'
            mock_get.side_effect = [
                # Simulate successful response for fetching release
                type(
                    "Response",
                    (object,),
                    {
                        "status_code": 200,
                        "content": b'{"assets": [{"name": "restic_fake_os.bz2", "browser_download_url": "https://example.com/restic_fake_os.bz2"}]}',
                        "raise_for_status": lambda x: True,
                    },
                )(),
                # Simulate exception during program download
                installer.requests.exceptions.MissingSchema("Invalid URL ''"),
            ]
            self.assertRaises(
                installer.requests.exceptions.MissingSchema, installer.download_restic
            )

    def test_download_restic_request_exception_fetch_release(self):
        # Mock the requests.get method to simulate a request exception
        with (
            patch(
                "runrestic.restic.installer.requests.get",
                side_effect=installer.requests.exceptions.RequestException(
                    "Request failed"
                ),
            ),
        ):
            self.assertRaises(
                installer.requests.exceptions.RequestException,
                installer.download_restic,
            )

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
            ) as mock_get,
        ):
            self.assertRaises(
                installer.requests.exceptions.RequestException,
                installer.download_restic,
            )
            self.assertEqual(mock_get.call_count, 2)
