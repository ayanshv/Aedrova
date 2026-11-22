import hashlib
import sys
from urllib.parse import urlsplit


class SessionVaultUnavailable(Exception):
    pass


class SessionVault:
    def __init__(self, origin, backend):
        self.backend = backend
        url = urlsplit(origin)
        scope = hashlib.sha256(f"{url.scheme}://{url.netloc.lower()}".encode()).hexdigest()
        self.scope = scope

    @classmethod
    def for_connection(cls, connection):
        if sys.platform == "darwin":
            from keyring.backends.macOS import Keyring

            backend = Keyring()
            backend.keychain = None
        elif sys.platform == "win32":
            from keyring.backends.Windows import WinVaultKeyring

            backend = WinVaultKeyring()
            backend.persist = "local machine"
        else:
            return None
        return cls(connection.url, backend)

    def _service(self, slot):
        return f"com.aedrova.session.{self.scope}.{slot}"

    def read(self, slot):
        try:
            return self.backend.get_password(self._service(slot), "refresh")
        except Exception:
            raise SessionVaultUnavailable from None

    def save(self, slot, token):
        try:
            self.backend.set_password(self._service(slot), "refresh", token)
            return True
        except Exception:
            return False

    def discard(self, slot):
        try:
            if self.read(slot) is not None:
                self.backend.delete_password(self._service(slot), "refresh")
            return True
        except Exception:
            return False
