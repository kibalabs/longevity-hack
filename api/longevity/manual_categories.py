"""Manual trait categorization mapping from categories_spiros.csv"""

from typing import Dict
from typing import Tuple

# Hardcoded manual categories mapping (RSID, trait) tuples to expert-curated categories
# Based on categories_spiros.csv - trait-specific to handle pleiotropic SNPs
# Format: (rsid, trait_name) -> category
MANUAL_CATEGORIES: Dict[Tuple[str, str], str] = {
    # Alzheimer's disease
    ('rs429358', "Alzheimer's disease"): 'Alzheimer',
    ('rs7412', "Alzheimer's disease"): 'Alzheimer',
    ('rs3851179', "Alzheimer's disease"): 'Alzheimer',
    ('rs744373', "Alzheimer's disease"): 'Alzheimer',
    ('rs11136000', "Alzheimer's disease"): 'Alzheimer',
    ('rs3764650', "Alzheimer's disease"): 'Alzheimer',
    ('rs6656401', "Alzheimer's disease"): 'Alzheimer',
    ('rs11218343', "Alzheimer's disease"): 'Alzheimer',
    ('rs75932628', "Alzheimer's disease"): 'Alzheimer',
    # Coronary artery disease
    ('rs11591147', 'Coronary artery disease'): 'Cardiological',
    ('rs6511720', 'Coronary artery disease'): 'Cardiological',
    ('rs10455872', 'Coronary artery disease'): 'Cardiological',
    ('rs1333049', 'Coronary artery disease'): 'Cardiological',
    ('rs9349379', 'Coronary artery disease'): 'Cardiological',
    ('rs9818870', 'Coronary artery disease'): 'Cardiological',
    ('rs1746048', 'Coronary artery disease'): 'Cardiological',
    ('rs11556924', 'Coronary artery disease'): 'Cardiological',
    ('rs579459', 'Coronary artery disease'): 'Cardiological',
    ('rs11206510', 'Coronary artery disease'): 'Cardiological',
    # Cholesterol and lipids
    ('rs12740374', 'LDL cholesterol'): 'Cardiological',
    ('rs12916', 'LDL cholesterol'): 'Cardiological',
    ('rs58542926', 'LDL cholesterol'): 'Cardiological',
    ('rs693', 'LDL cholesterol'): 'Cardiological',
    ('rs12678919', 'Triglycerides'): 'Cardiological',
    ('rs780094', 'Triglycerides'): 'Cardiological',
    ('rs10468017', 'HDL cholesterol'): 'Cardiological',
    ('rs3764261', 'HDL cholesterol'): 'Cardiological',
    # Stroke
    ('rs2107595', 'Large-artery ischemic stroke'): 'Cardiological',
    # Heart failure
    ('rs1739843', 'Heart failure'): 'Cardiological',
    ('rs2234962', 'Heart failure'): 'Cardiological',
    # Hypertension
    ('rs11191548', 'Hypertension'): 'Cardiological',
    ('rs198389', 'Hypertension'): 'Cardiological',
    # Type 2 diabetes
    ('rs7903146', 'Type 2 diabetes'): 'T2D',
    ('rs5219', 'Type 2 diabetes'): 'T2D',
    ('rs13266634', 'Type 2 diabetes'): 'T2D',
    ('rs7756992', 'Type 2 diabetes'): 'T2D',
    ('rs4402960', 'Type 2 diabetes'): 'T2D',
    ('rs10811661', 'Type 2 diabetes'): 'T2D',
    ('rs2237892', 'Type 2 diabetes'): 'T2D',
    ('rs1801282', 'Type 2 diabetes'): 'T2D',
    # Body mass index / Obesity
    ('rs9939609', 'Body mass index'): 'Obesity_BMI',
    ('rs17782313', 'Body mass index'): 'Obesity_BMI',
    ('rs1558902', 'Body mass index'): 'Obesity_BMI',
    # Fasting glucose
    ('rs16926246', 'Fasting glucose'): 'Obesity_BMI',
    ('rs560887', 'Fasting glucose'): 'Obesity_BMI',
    # Chronic kidney disease
    ('rs12917707', 'Chronic kidney disease'): 'CKD',
    ('rs17319721', 'Chronic kidney disease'): 'CKD',
    ('rs1150459', 'Chronic kidney disease'): 'CKD',
    # Atrial fibrillation
    ('rs2200733', 'Atrial fibrillation'): 'AF',
    ('rs2106261', 'Atrial fibrillation'): 'AF',
    ('rs13376333', 'Atrial fibrillation'): 'AF',
    # Inflammation (C-reactive protein)
    ('rs1800795', 'C-reactive protein'): 'Inflammation',
    ('rs2228145', 'C-reactive protein'): 'Inflammation',
    ('rs1205', 'C-reactive protein'): 'Inflammation',
    # Parkinson's disease
    ('rs34637584', "Parkinson's disease"): 'Parkinson',
    ('rs356219', "Parkinson's disease"): 'Parkinson',
    ('rs2230288', "Parkinson's disease"): 'Parkinson',
    # Lung cancer
    ('rs2736100', 'Lung cancer'): 'Lung Cancer',
    ('rs16969968', 'Lung cancer'): 'Lung Cancer',
    # Colorectal cancer
    ('rs6983267', 'Colorectal cancer'): 'Colorectal Cancer',
    ('rs4939827', 'Colorectal cancer'): 'Colorectal Cancer',
    ('rs4779584', 'Colorectal cancer'): 'Colorectal Cancer',
    # Breast cancer
    ('rs3803662', 'Breast cancer (female)'): 'Breast Cancer',
    ('rs2981582', 'Breast cancer (female)'): 'Breast Cancer',
    ('rs13281615', 'Breast cancer (female)'): 'Breast Cancer',
    ('rs17468277', 'Breast cancer (female)'): 'Breast Cancer',
    # Prostate cancer
    ('rs2735839', 'Prostate cancer (male)'): 'Prostate Cancer',
    ('rs138213197', 'Prostate cancer (male)'): 'Prostate Cancer',
    # Pancreatic cancer
    ('rs505922', 'Pancreatic cancer'): 'Pancreatic Cancer',
    # Melanoma
    ('rs1805007', 'Melanoma'): 'Melanoma',
    # Osteoarthritis
    ('rs143383', 'Osteoarthritis'): 'Osteoarthritis',
    # Bone mineral density / Osteoporosis
    ('rs3736228', 'Bone mineral density'): 'Osteoporosis',
    ('rs4355801', 'Bone mineral density'): 'Osteoporosis',
    ('rs851056', 'Bone mineral density'): 'Osteoporosis',
    # Grip strength / Sarcopenia
    ('rs55872725', 'Grip strength'): 'Sarcopenia',
    ('rs12928404', 'Grip strength'): 'Sarcopenia',
    # Exceptional longevity
    ('rs2802292', 'Exceptional longevity'): 'Longevity',
    # Parental lifespan
    ('rs429358', 'Parental lifespan'): 'General Longevity',
    ('rs7412', 'Parental lifespan'): 'General Longevity',
    # DNAm GrimAge acceleration
    ('rs2736100', 'DNAm GrimAge acceleration'): 'General Longevity',
    # All-cause mortality
    ('rs1799945', 'All-cause mortality'): 'General Longevity',
}


def get_manual_category(rsid: str, trait: str | None = None) -> str | None:
    """
    Get the manual category for an RSID and trait combination.

    Args:
        rsid: The RSID to look up
        trait: The specific trait/disease name (optional for backwards compatibility)

    Returns:
        The manual category string, or None if not found
    """
    if trait is None:
        # Backwards compatibility: if no trait specified, return None
        return None

    # Normalize trait name (case-insensitive lookup)
    lookup_key = (rsid, trait)
    category = MANUAL_CATEGORIES.get(lookup_key)

    if category is None:
        # Try case-insensitive match
        rsid_lower = rsid.lower()
        trait_lower = trait.lower()
        for (key_rsid, key_trait), value in MANUAL_CATEGORIES.items():
            if key_rsid.lower() == rsid_lower and key_trait.lower() == trait_lower:
                return value

    return category
