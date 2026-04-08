from __future__ import annotations

from just_bash import Bash


def main() -> None:
    with Bash(
        network={
            "allowedUrlPrefixes": [
                "http://example.com",
            ],
        }
    ) as bash:
        result = bash.exec("curl -s http://example.com | html-to-markdown | head -n 12")
        print(result.stdout, end="")


if __name__ == "__main__":
    main()
