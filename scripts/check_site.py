"""Check the files and references used by the static landing page."""

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]


class SiteParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.references = []
        self.stylesheets = set()
        self.errors = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        line = self.getpos()[0]
        element_id = attributes.get("id")
        if element_id:
            if element_id in self.ids:
                self.errors.append(f"Line {line}: duplicate id {element_id!r}")
            self.ids.add(element_id)

        if tag == "img":
            if not attributes.get("src"):
                self.errors.append(f"Line {line}: image has no src")
            if attributes.get("alt") is None:
                self.errors.append(f"Line {line}: image has no alt attribute")
        if tag == "link" and "stylesheet" in (attributes.get("rel") or "").split():
            self.stylesheets.add(attributes.get("href"))

        for attribute in ("href", "src"):
            if attributes.get(attribute):
                self.references.append((line, attributes[attribute]))


def main():
    parser = SiteParser()
    parser.feed((ROOT / "index.html").read_text(encoding="utf-8"))
    parser.close()

    stylesheet = ROOT / "style.css"
    if "style.css" not in parser.stylesheets:
        parser.errors.append("index.html must link to style.css")
    if not stylesheet.is_file() or not stylesheet.read_text(encoding="utf-8").strip():
        parser.errors.append("style.css is missing or empty")

    for line, reference in parser.references:
        url = urlsplit(reference)
        if url.scheme or url.netloc:
            continue
        if url.path:
            target = (ROOT / unquote(url.path)).resolve()
            if not target.is_relative_to(ROOT) or not target.is_file():
                parser.errors.append(f"Line {line}: missing local file {url.path!r}")
        elif url.fragment and unquote(url.fragment) not in parser.ids:
            parser.errors.append(f"Line {line}: missing anchor #{url.fragment}")

    if parser.errors:
        raise SystemExit("\n".join(parser.errors))
    print("Site checks passed: stylesheet, local files, anchors, IDs and image alt attributes.")


if __name__ == "__main__":
    main()
