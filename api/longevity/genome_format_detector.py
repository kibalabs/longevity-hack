"""Detect genome file formats (23andMe, Ancestry, VCF, etc.)."""


def detect_genome_format_from_filename(fileName: str) -> str:
    """
    Detect the format of a genome file based on its filename.
    This is a lightweight detection for when file content isn't available yet.

    Returns:
        "23andme" | "ancestry" | "vcf" | "unknown"
    """
    lowerName = fileName.lower()

    if '23andme' in lowerName or '23-and-me' in lowerName:
        return '23andme'
    if 'ancestry' in lowerName:
        return 'ancestry'
    if lowerName.endswith('.vcf') or lowerName.endswith('.vcf.gz'):
        return 'vcf'
    if lowerName.endswith('.txt') or lowerName.endswith('.csv'):
        # Could be either 23andme or ancestry, default to unknown
        return 'unknown'

    return 'unknown'


def detect_genome_format(fileContent: str) -> str:
    """
    Detect the format of a genome file based on its content.

    Returns:
        "23andme" | "ancestry" | "vcf" | "unknown"
    """
    lines = fileContent.split('\n')

    # Check first few lines for format indicators
    headerFound = False
    dataLinesChecked = 0
    validDataLines = 0
    firstLine = True

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # VCF format detection
        if stripped.startswith('##fileformat=VCF'):
            return 'vcf'

        # 23andMe format detection - check for header with or without #
        if stripped.startswith('#') or firstLine:
            lower = stripped.lower()
            if 'rsid' in lower and 'chromosome' in lower and 'position' in lower and 'genotype' in lower:
                headerFound = True
                firstLine = False
                continue
            if stripped.startswith('#'):
                firstLine = False
                continue

        firstLine = False

        # Check data lines for 23andMe format
        if dataLinesChecked < 10:
            parts = stripped.split('\t')
            if len(parts) >= 4:
                rsid, chromosome, position, genotype = parts[:4]
                # Validate rsid format (rs* or i*)
                if rsid.startswith('rs') or rsid.startswith('i'):
                    # Validate chromosome (1-22, X, Y, MT)
                    if chromosome in [str(i) for i in range(1, 23)] + ['X', 'Y', 'MT']:
                        # Validate position is numeric
                        if position.isdigit():
                            # Validate genotype (length 2, or --)
                            if len(genotype) == 2:
                                validDataLines += 1

            dataLinesChecked += 1
            if dataLinesChecked >= 10:
                break

    # 23andMe if we found the header and at least 5 valid data lines
    if headerFound and validDataLines >= 5:
        return '23andme'

    return 'unknown'
