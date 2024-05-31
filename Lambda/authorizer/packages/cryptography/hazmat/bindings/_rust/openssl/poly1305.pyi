# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the BSD License. See the LICENSE file in the root of this repository
# for complete details.

class Poly1305:
    def __init__(self, key: bytes) -> None: ...
    @staticmethod
    def generate_tag(key: bytes, data: bytes) -> bytes: ...
    @staticmethod
    def verify_tag(key: bytes, data: bytes, tag: bytes) -> None: ...
    def update(self, data: bytes) -> None: ...
    def finalize(self) -> bytes: ...
    def verify(self, tag: bytes) -> None: ...