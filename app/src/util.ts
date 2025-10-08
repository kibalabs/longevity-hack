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
