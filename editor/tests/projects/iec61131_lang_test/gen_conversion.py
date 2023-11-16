
# Naive code generator for type convesion function XX_TO_YY testing


types = [
    ("BOOL", "TRUE"),
    ("SINT", "42"),
    ("USINT", "42"),
    ("BYTE", "42"),
    ("STRING", "'42'"),
    ("INT", "42"),
    ("UINT", "42"),
    ("WORD", "42"),
    ("DINT", "42"),
    ("UDINT", "42"),
    ("DWORD", "42"),
    ("LINT", "42"),
    ("ULINT", "42"),
    ("LWORD", "42"),
    ("REAL", "42.0"),
    ("LREAL", "42.0"),
    #("TIME", "42"),
    #("TOD", "42"),
    #("DATE", "42"),
    #("DT", "42"),
]

for tsrc, src_literal in types:
    for tdest, dest_literal in types:
        if tsrc == tdest: continue
        s = f"""
RESULT := '{tsrc}_TO_{tdest}'; 
IF {tsrc}_TO_{tdest}({tsrc}#{src_literal}) <> {tdest}#{dest_literal} THEN RETURN; END_IF;
"""
        print(s)


