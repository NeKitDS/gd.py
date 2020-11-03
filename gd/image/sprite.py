from attr import attrib, dataclass

from gd.typing import Optional, Set, TypeVar, TYPE_CHECKING

from gd.image.geometry import Point, Size, Rectangle

__all__ = ("Sprite",)

COPY_SUFFIX = "_copy"

if TYPE_CHECKING:
    from gd.image.sheet import Sheet  # noqa

SP = TypeVar("SP", bound="Sprite")


@dataclass
class Sprite:
    name: str = attrib()
    aliases: Set[str] = attrib(factory=set)
    relative_offset: Point = attrib(factory=Point)
    size: Size = attrib(factory=Size)
    source_size: Size = attrib(factory=Size)
    rectangle: Rectangle = attrib(factory=Rectangle)
    rotated: bool = attrib(default=False)
    copy_level: int = attrib(default=0)
    sheet_unchecked: Optional["Sheet"] = attrib(default=None)

    def __str__(self) -> str:
        return self.name_with_copy

    def invert_size(self: SP) -> SP:
        self.size.invert()
        self.source_size.invert()
        self.rectangle.invert_size()

        return self

    def inverted_size(self: SP) -> SP:
        return self.__class__(
            name=self.name,
            aliases=self.aliases,
            relative_offset=self.relative_offset,
            size=self.size.inverted(),
            source_size=self.source_size.inverted(),
            rectangle=self.rectangle.inverted_size(),
            rotated=self.rotated,
            copy_level=self.next_copy_level,
            sheet_unchecked=self.sheet_unchecked,
        )

    @property
    def name_with_copy(self) -> str:
        return self.name + COPY_SUFFIX * self.copy_level

    @property
    def next_copy_level(self) -> int:
        return self.copy_level + 1

    @property
    def offset(self) -> Point:
        return self.relative_offset.__class__(
            self.relative_offset.x + (self.source_size.width - self.rectangle.width) / 2,
            self.relative_offset.y - (self.source_size.height - self.rectangle.height) / 2,
        )

    def get_sheet(self) -> "Sheet":
        result = self.sheet_unchecked

        if result is None:
            raise ValueError(f"Sheet is not attached to {self.name_with_copy}.")

        return result

    def set_sheet(self, sheet: "Sheet") -> None:
        self.sheet_unchecked = sheet

    def delete_sheet(self) -> None:
        self.sheet_unchecked = None

    sheet = property(get_sheet, set_sheet, delete_sheet)

    def attach_sheet(self: SP, sheet: "Sheet") -> SP:
        self.sheet = sheet

        return self

    def detach_sheet(self: SP) -> SP:
        del self.sheet

        return self

    def is_rotated(self) -> bool:
        return self.rotated

    def copy(self) -> "Sprite":
        return self.__class__(
            name=self.name,
            aliases=self.aliases,
            relative_offset=self.relative_offset,
            size=self.size,
            source_size=self.source_size,
            rectangle=self.rectangle,
            rotated=self.rotated,
            copy_level=self.next_copy_level,
            sheet_unchecked=self.sheet_unchecked,
        )