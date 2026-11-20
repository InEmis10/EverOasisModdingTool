from io import TextIOWrapper, BufferedRandom, BufferedReader
from pathlib import Path
import struct

FILE_TYPE = 4
FILE_TYPE_TARTGET_VALUE = b"bdb\0" #note pour plus tard b operator == string ou valeur mais convertie en binaire
UNK1 = 4 ##list id ???
FVERSION = 2
COLUMNS = 2
LINE_SIZE = 2 #returned value is in octet
LINE_COUNT = 2
NFIX = 2 ## colums / blob ou je sais pas trop quoi miskine
HASH_INDEX_SIZE = 2

DATA_DEF = 0x20 #<=> 4+4+2+2+2+2+2+2

ZONE_SIZE = 2
ZONE_COUNT = 5
PADDING = 2


def _readHeader(f : BufferedRandom):
    header = {}
    fileType = f.read(FILE_TYPE)
    if not fileType == FILE_TYPE_TARTGET_VALUE:
        return None
    header["unk1"] = int.from_bytes(f.read(UNK1) , "little")
    header["version"] = int.from_bytes(f.read(FVERSION), "little")
    header["columns"] = int.from_bytes(f.read(COLUMNS), "little")
    header["lineSize"] = int.from_bytes(f.read(LINE_SIZE), "little")
    header["lineCount"] = int.from_bytes(f.read(LINE_COUNT), "little")
    header["nfix"] = int.from_bytes(f.read(NFIX), "little")
    header["hashInexSize"] = int.from_bytes(f.read(HASH_INDEX_SIZE), "little")
    header["zone"] = [int.from_bytes(f.read(ZONE_SIZE), "little") * 4 for _ in range(ZONE_COUNT)]
    f.read(PADDING)
    return header

COL_TYPE = 2
COL_OFFSET = 2

def _readDef(f : BufferedRandom | BufferedReader, header):
    cols = []
    for _ in range(header["columns"]):
        ztype = int.from_bytes(f.read(COL_TYPE), "little")
        zoffset = int.from_bytes(f.read(COL_OFFSET), "little")
        cols.append([ztype, zoffset])
    return cols

TYPE_FORMAT = {
    0: "<b",   # s8
    1: "<h",   # s16
    2: "<i",   # s32
    3: "<B",   # u8
    4: "<H",   # u16
    5: "<I",   # u32
    6: "<f",   # float
    7: "<?",   # bool
    14: "<I",  # chaîne (offset)
    15: "<I",  # blob
}

def _readData(f : BufferedRandom | BufferedReader, header, dbd_def):
    f.seek(header["zone"][4])
    rows = []
    for _ in range(header["lineCount"]):
        line = f.read(header["lineSize"])
        row = []
        for typ, off in dbd_def:
            value = struct.unpack_from(TYPE_FORMAT[typ], line, off)[0]
            row.append(value)
        rows.append(row)
    return rows

TYPE_NAME = {0: "s8", 1: "s16", 2: "s32", 3: "u8", 4: "u16", 5: "u32", 6: "f32", 7: "bool", 14: "str", 15: "blob"}

STRING_KIND = 1  # genre 1 dans la zone 0 = chaîne (zone 1), genre 0 = blob (zone 2)

def _readFixes(f : BufferedRandom | BufferedReader, header):
    """Zone 0 : {colonne: (genre, [offset par ligne])}. Pour ces colonnes, la valeur dans la ligne n'est pas fiable."""
    nfix, nrows = header["nfix"], header["lineCount"]
    f.seek(header["zone"][0])
    desc = [struct.unpack("<2H", f.read(4)) for _ in range(nfix)]
    values = struct.unpack(f"<{nrows * nfix}H", f.read(2 * nrows * nfix))
    return {col: (kind, [values[r * nfix + j] for r in range(nrows)]) for j, (col, kind) in enumerate(desc)}

def _readStrings(f : BufferedRandom | BufferedReader, header, rows, fixes):
    """Remplace l'offset des colonnes chaîne par le texte lu dans la zone 1."""
    f.seek(header["zone"][1])
    pool = f.read(header["zone"][2] - header["zone"][1])
    for col, (kind, offsets) in fixes.items():
        if kind != STRING_KIND:
            continue
        for row, off in zip(rows, offsets):
            end = pool.find(b"\0", off)
            row[col] = pool[off:end if end >= 0 else None].decode("ascii", "replace")

def _formatCell(value) -> str:
    if isinstance(value, float):
        return f"{value:g}"
    if isinstance(value, str):
        return f'"{value}"'
    return str(value)

class BdbFile:
    def __init__(self, header, bdb_def, data, path : Path):
        self.header = header
        self.BdbDef = bdb_def
        self.data = data
        self.Path = path
        self.Name = path.name
        self.mapping = self._mapFile()

    def _mapFile(self):
        ##TODO: .cache , tags : (tags == mapping des nom des valeurs et ensuite faire une table pour display les noms
        # en attendant : "id" pour la colonne 0, sinon le n° de colonne
        return ["id"] + [f"c{i}" for i in range(1, len(self.BdbDef))]

    def render(self) -> str:
        """Table en texte aligné, affichée dans un CodeView comme les scripts."""
        header = [f"{name}:{TYPE_NAME.get(typ, typ)}" for name, (typ, _) in zip(self.mapping, self.BdbDef)]
        cells = [[_formatCell(v) for v in row] for row in self.data]
        widths = [max([len(header[c])] + [len(row[c]) for row in cells]) for c in range(len(header))]
        lines = [" | ".join(h.ljust(w) for h, w in zip(header, widths)),
                 "-+-".join("-" * w for w in widths)]
        lines += [" | ".join(v.ljust(w) for v, w in zip(row, widths)) for row in cells]
        return "\n".join(lines)

class BdbReader:
    @classmethod
    def read(cls, path : Path) -> BdbFile | None:
        path = Path(path).expanduser()
        if not path.is_file():
            return None
        with open(path, "rb") as f:
            header = _readHeader(f)
            if header is None:
                return None
            bdb_def = _readDef(f, header)
            if not bdb_def:
                return None
            data = _readData(f, header, bdb_def)
            _readStrings(f, header, data, _readFixes(f, header))
            return BdbFile(header, bdb_def, data, path)


# test manuel : python -m src.bin.tools.DbdReader (ne s'exécute pas à l'import)
if __name__ == "__main__":
    bdb = BdbReader.read(Path("~/EverOasisProject/workspace/base/extracted/data/database.gar_x/spiritlevel_database.bdb"))
    print(bdb.header)
    print(bdb.render())





