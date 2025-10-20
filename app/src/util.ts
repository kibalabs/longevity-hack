import { shortFormatNumber } from '@kibalabs/core';

export const bigIntMax = (...args: bigint[]): bigint => {
  if (args.length === 0) {
    throw new Error('bigIntMax requires at least one argument');
  }
  let max = args[0];
  for (let i = 1; i < args.length; i += 1) {
    if (args[i] > max) {
      max = args[i];
    }
  }
  return max;
};

export const assetValueToNumber = (value: bigint, decimals: number, precision: number = 18): number => {
  const divisor = 10 ** precision;
  return Number((value * BigInt(divisor)) / BigInt(10) ** BigInt(decimals)) / divisor;
};

export const decimalWithCommas = (value: number, decimalPrecision: number = 3): string => {
  const fixedValue = value.toFixed(decimalPrecision);
  const parts = fixedValue.split('.');
  const integerPart = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  const decimalPart = parts.length > 1 ? parts[1] : undefined;
  return decimalPart !== undefined ? `${integerPart}.${decimalPart}` : integerPart;
};

export const shortFormatDollars = (value: number): string => {
  const valueString = shortFormatNumber(Math.abs(value));
  return `${value < 0 ? '-' : ''}$${valueString}`;
};

export const calculateDiffDays = (date1: Date, date2: Date): number => {
  const differenceInTime = date2.getTime() - date1.getTime();
  const differenceInDays = differenceInTime / (1000 * 3600 * 24);
  return Math.abs(Math.round(differenceInDays));
};

export interface ImportanceBucket {
  label: string;
  level: 'critical' | 'high' | 'moderate' | 'low';
  backgroundColor: string;
  color: string;
}

export const getImportanceBucket = (score: number): ImportanceBucket => {
  if (score >= 50) {
    return {
      label: 'Very Strong',
      level: 'critical',
      backgroundColor: '#FFEBEE',
      color: '#C62828',
    };
  } else if (score >= 30) {
    return {
      label: 'Strong',
      level: 'high',
      backgroundColor: '#FFF3E0',
      color: '#E65100',
    };
  } else if (score >= 15) {
    return {
      label: 'Moderate',
      level: 'moderate',
      backgroundColor: '#FFF9C4',
      color: '#F57F17',
    };
  } else {
    return {
      label: 'Weak',
      level: 'low',
      backgroundColor: '#E3F2FD',
      color: '#1565C0',
    };
  }
};

export interface RiskBucket {
  label: string;
  backgroundColor: string;
  color: string;
}

export const getRiskBucket = (riskLevel: string | undefined | null): RiskBucket => {
  switch (riskLevel) {
    case 'very_high':
      return {
        label: 'Very High Risk',
        backgroundColor: '#FFEBEE',
        color: '#C62828',
      };
    case 'high':
      return {
        label: 'High Risk',
        backgroundColor: '#FFE0B2',
        color: '#E65100',
      };
    case 'moderate':
      return {
        label: 'Moderately Higher Risk',
        backgroundColor: '#FFF9C4',
        color: '#F57F17',
      };
    case 'slight':
      return {
        label: 'Slightly Higher Risk',
        backgroundColor: '#E3F2FD',
        color: '#1976D2',
      };
    case 'lower':
      return {
        label: 'Lower Risk',
        backgroundColor: '#E8F5E9',
        color: '#2E7D32',
      };
    default:
      return {
        label: 'Unknown Risk',
        backgroundColor: '#F5F5F5',
        color: '#666666',
      };
  }
};

export const getRiskPriority = (riskLevel: string | undefined | null): number => {
  switch (riskLevel) {
    case 'very_high':
      return 100;
    case 'high':
      return 90;
    case 'moderate':
      return 75;
    case 'slight':
      return 55;
    case 'lower':
      return 1;
    default:
      return 0;
  }
};
