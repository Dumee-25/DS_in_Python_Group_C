import re
from abc import ABC, abstractmethod

from shared.contracts import Chunk


class BaseChunker(ABC):

    @abstractmethod
    def chunk(self, text: str, source_doc: str, collection: str,
              snapshot_date: str, in_force: bool) -> list[Chunk]: ...


class SectionAwareChunker(BaseChunker):
   
    SECTION_RE = re.compile(r"(?m)^\s*(\d{1,3})\.\s")   # top-level sections

    def chunk(self, text, source_doc, collection, snapshot_date, in_force):
        chunks, spans = [], []
        matches = list(self.SECTION_RE.finditer(text))
        for i, m in enumerate(matches):
            start = m.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            spans.append((f"s.{m.group(1)}", text[start:end].strip()))
        for section, body in spans:
            
            for piece in self._split_long(body, max_chars=1800, overlap_chars=200):
                chunks.append(Chunk(text=piece, source_doc=source_doc,
                                    section=section, collection=collection,
                                    snapshot_date=snapshot_date, in_force=in_force))
        return chunks

    @staticmethod
    def _split_long(body: str, max_chars: int, overlap_chars: int) -> list[str]:
        if len(body) <= max_chars:
            return [body]
        pieces, start = [], 0
        while start < len(body):
            pieces.append(body[start:start + max_chars])
            start += max_chars - overlap_chars
        return pieces


class RecursiveChunker(BaseChunker):


    def __init__(self, size: int = 1200, overlap: int = 200):
        self.size, self.overlap = size, overlap

    def chunk(self, text, source_doc, collection, snapshot_date, in_force):
        out, start = [], 0
        while start < len(text):
            out.append(Chunk(text=text[start:start + self.size], source_doc=source_doc,
                             section="", collection=collection,
                             snapshot_date=snapshot_date, in_force=in_force))
            start += self.size - self.overlap
        return out

