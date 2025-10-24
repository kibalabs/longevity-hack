from enum import Enum

class GenomeFileFormat(Enum):
    TWENTY_THREE_AND_ME = '23andMe'
    MY_HERITAGE = 'MyHeritage'
    UNKNOWN = 'Unknown'


def detect_format(content: str) -> GenomeFileFormat:
    """
    Detects the genome file format by inspecting the first few lines of the content.
    """
    lines = content.splitlines()
    if not lines:
        return GenomeFileFormat.UNKNOWN

    # Check for MyHeritage format (CSV with specific header)
    if any('MyHeritage DNA raw data' in line for line in lines[:10]):
        return GenomeFileFormat.MY_HERITAGE

    # Check for 23andMe format (TSV with specific comment header)
    is_23andme = False
    for line in lines[:100]:
        if line.startswith('#'):
            if 'rsid' in line and 'chromosome' in line and 'position' in line:
                is_23andme = True
                break
        # Check for tab-separated data which is also a strong indicator
        elif '\t' in line:
            parts = line.split('\t')
            if len(parts) >= 4 and (parts[0].startswith('rs') or parts[0].startswith('i')):
                is_23andme = True
                break

    if is_23andme:
        return GenomeFileFormat.TWENTY_THREE_AND_ME

    return GenomeFileFormat.UNKNOWN
