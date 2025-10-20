import React from 'react';

import { useNavigator } from '@kibalabs/core-react';
import { Alignment, Direction, PaddingSize, Stack, Text } from '@kibalabs/ui-react';

import * as Resources from '../client/resources';
import { useGlobals } from '../GlobalsContext';
import { getRiskBucket, getRiskPriority } from '../util';

interface CategorySnpsData {
  snps: Resources.SNP[];
  totalCount: number;
  hasMore: boolean;
  isLoading: boolean;
}

export function ResultsPage(): React.ReactElement {
  const navigator = useNavigator();
  const { longevityClient } = useGlobals();
  const [genomeAnalysisId, setGenomeAnalysisId] = React.useState<string | null>(null);
  const [overview, setOverview] = React.useState<Resources.GenomeAnalysisOverview | null>(null);
  const [expandedGroups, setExpandedGroups] = React.useState<Set<string>>(new Set());
  const [categorySnpsData, setCategorySnpsData] = React.useState<Map<string, CategorySnpsData>>(new Map());

  React.useEffect((): void => {
    const urlParams = new URLSearchParams(window.location.search);
    const id = urlParams.get('id');
    if (id) {
      setGenomeAnalysisId(id);
      longevityClient.getGenomeAnalysisOverview(id).then((overviewData: Resources.GenomeAnalysisOverview): void => {
        setOverview(overviewData);
      }).catch((error: Error): void => {
        console.error('Failed to fetch overview:', error);
      });
    } else {
      navigator.navigateTo('/');
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const sortSnps = (snps: Resources.SNP[]): Resources.SNP[] => {
    return [...snps].sort((a, b) => {
      const priorityA = getRiskPriority(a.riskLevel);
      const priorityB = getRiskPriority(b.riskLevel);

      if (priorityB !== priorityA) {
        return priorityB - priorityA;
      }

      const scoreA = a.importanceScore ?? 0;
      const scoreB = b.importanceScore ?? 0;
      return scoreB - scoreA;
    });
  };

  const toggleGroup = (groupId: string, group: Resources.GenomeAnalysisCategoryGroup): void => {
    setExpandedGroups((prev): Set<string> => {
      const newSet = new Set(prev);
      const wasExpanded = newSet.has(groupId);

      if (wasExpanded) {
        newSet.delete(groupId);
      } else {
        newSet.add(groupId);
        // Initialize with top 5 SNPs if not already loaded
        if (!categorySnpsData.has(groupId)) {
          setCategorySnpsData((prevData): Map<string, CategorySnpsData> => {
            const newMap = new Map(prevData);
            newMap.set(groupId, {
              snps: sortSnps(group.topSnps),
              totalCount: group.totalCount,
              hasMore: group.totalCount > 5,
              isLoading: false,
            });
            return newMap;
          });
        }
      }
      return newSet;
    });
  };

  const loadMore = async (genomeAnalysisResultId: string): Promise<void> => {
    if (!genomeAnalysisId) return;

    const currentData = categorySnpsData.get(genomeAnalysisResultId);
    if (!currentData || currentData.isLoading) return;

    // Set loading state
    setCategorySnpsData((prev): Map<string, CategorySnpsData> => {
      const newMap = new Map(prev);
      const data = newMap.get(genomeAnalysisResultId);
      if (data) {
        newMap.set(genomeAnalysisResultId, { ...data, isLoading: true });
      }
      return newMap;
    });

    try {
      const offset = currentData.snps.length;
      const page = await longevityClient.listCategorySnps(genomeAnalysisId, genomeAnalysisResultId, offset, 20);

      setCategorySnpsData((prev): Map<string, CategorySnpsData> => {
        const newMap = new Map(prev);
        const existingData = newMap.get(genomeAnalysisResultId);
        if (existingData) {
          const allSnps = sortSnps([...existingData.snps, ...page.snps]);
          newMap.set(genomeAnalysisResultId, {
            snps: allSnps,
            totalCount: page.totalCount,
            hasMore: allSnps.length < page.totalCount,
            isLoading: false,
          });
        }
        return newMap;
      });
    } catch (error) {
      console.error('Failed to load more SNPs:', error);
      // Reset loading state on error
      setCategorySnpsData((prev): Map<string, CategorySnpsData> => {
        const newMap = new Map(prev);
        const data = newMap.get(genomeAnalysisResultId);
        if (data) {
          newMap.set(genomeAnalysisResultId, { ...data, isLoading: false });
        }
        return newMap;
      });
    }
  };

  if (!overview) {
    return (
      <Stack direction={Direction.Vertical} isFullWidth={true} isFullHeight={true} childAlignment={Alignment.Center} contentAlignment={Alignment.Center}>
        <Text variant='default'>Loading results...</Text>
      </Stack>
    );
  }

  return (
    <Stack direction={Direction.Vertical} isFullWidth={true} isFullHeight={true}>
      {/* Compact Header */}
      <div style={{ borderBottom: '1px solid #E5E5E5', backgroundColor: '#FAFAFA' }}>
        <Stack
          direction={Direction.Horizontal}
          contentAlignment={Alignment.Center}
          childAlignment={Alignment.Center}
          shouldAddGutters={true}
          paddingVertical={PaddingSize.Wide}
          paddingHorizontal={PaddingSize.Wide}
        >
          <Text variant='header3'>🧬 Genome Analysis</Text>
          {overview.summary && (
            <>
              <Text variant='note'>•</Text>
              <Text variant='note'>{overview.summary.matchedSnps?.toLocaleString()} associations</Text>
              <Text variant='note'>•</Text>
              <Text variant='note'>{overview.categoryGroups.length} categories</Text>
              {overview.summary.clinvarCount && overview.summary.clinvarCount > 0 && (
                <>
                  <Text variant='note'>•</Text>
                  <Text variant='note'>⚕️ {overview.summary.clinvarCount} clinical</Text>
                </>
              )}
            </>
          )}
        </Stack>
      </div>

      {/* Scrollable Content */}
      <div style={{ flex: 1, overflowY: 'auto', width: '100%' }}>
        <Stack direction={Direction.Vertical} shouldAddGutters={true} defaultGutter={PaddingSize.Default} isFullWidth={true} paddingHorizontal={PaddingSize.Wide} paddingVertical={PaddingSize.Wide}>
          {overview.categoryGroups.map((group: Resources.GenomeAnalysisCategoryGroup): React.ReactElement => {
            const isExpanded = expandedGroups.has(group.genomeAnalysisResultId);
            const loadedData = categorySnpsData.get(group.genomeAnalysisResultId);
            const displaySnps = loadedData ? loadedData.snps : group.topSnps;
            const hasMore = loadedData ? loadedData.hasMore : group.totalCount > 5;

            return (
              <div
                key={group.genomeAnalysisResultId}
                style={{
                  border: '1px solid #E5E5E5',
                  borderRadius: '8px',
                  backgroundColor: 'white',
                  overflow: 'hidden',
                }}
              >
                {/* Group Header - Clickable */}
                <div
                  onClick={(): void => toggleGroup(group.genomeAnalysisResultId, group)}
                  style={{
                    padding: '12px 16px',
                    backgroundColor: '#F8F9FA',
                    cursor: 'pointer',
                    borderBottom: isExpanded ? '1px solid #E5E5E5' : 'none',
                    transition: 'background-color 0.2s',
                  }}
                  onMouseEnter={(e): void => { e.currentTarget.style.backgroundColor = '#F0F2F5'; }}
                  onMouseLeave={(e): void => { e.currentTarget.style.backgroundColor = '#F8F9FA'; }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Stack direction={Direction.Horizontal} shouldAddGutters={true} defaultGutter={PaddingSize.Wide} childAlignment={Alignment.Center}>
                      <Text variant='bold'>{group.phenotypeGroup}</Text>
                      <div style={{
                        backgroundColor: '#007AFF',
                        color: 'white',
                        padding: '2px 8px',
                        borderRadius: '12px',
                        fontSize: '12px',
                        fontWeight: 600,
                      }}>
                        {group.totalCount}
                      </div>
                    </Stack>
                    <Text variant='note'>{isExpanded ? '▼' : '▶'}</Text>
                  </div>
                  {!isExpanded && (
                    <div style={{ marginTop: '4px' }}>
                      <Text variant='note'>{group.phenotypeDescription}</Text>
                    </div>
                  )}
                </div>

                {/* Expanded Content */}
                {isExpanded && (
                  <div style={{ padding: '16px' }}>
                    <div style={{ marginBottom: '12px' }}>
                      <Text variant='note'>{group.phenotypeDescription}</Text>
                    </div>

                    <Stack direction={Direction.Vertical} shouldAddGutters={true} defaultGutter={PaddingSize.Default}>
                      {displaySnps.map((snp: Resources.SNP, index: number): React.ReactElement => (
                        <div
                          key={`${snp.rsid}-${index}`}
                          style={{
                            padding: '12px',
                            backgroundColor: 'white',
                            borderRadius: '6px',
                            border: '1px solid #E8EAED',
                          }}
                        >
                          {/* Top Row: rsid, genotype, and badges */}
                          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                            <div style={{
                              color: '#007AFF',
                              fontWeight: 600,
                              fontSize: '15px',
                              minWidth: '100px',
                            }}>
                              {snp.rsid}
                            </div>
                            <div style={{
                              backgroundColor: '#F5F5F5',
                              padding: '4px 10px',
                              borderRadius: '4px',
                              fontSize: '13px',
                              fontWeight: 500,
                            }}>
                              {snp.genotype}
                            </div>
                            {snp.importanceScore && snp.importanceScore > 15 && (
                              <div style={{
                                backgroundColor: '#FFEBEE',
                                color: '#C62828',
                                padding: '4px 8px',
                                borderRadius: '4px',
                                fontSize: '12px',
                                fontWeight: 600,
                                display: 'flex',
                                alignItems: 'center',
                                gap: '4px',
                              }}>
                                <span>⚠</span>
                              </div>
                            )}
                            {snp.clinvarCondition && snp.clinvarCondition !== 'not provided' && (
                              <div style={{
                                backgroundColor: '#FFF9C4',
                                color: '#F57F17',
                                padding: '4px 8px',
                                borderRadius: '4px',
                                fontSize: '12px',
                                fontWeight: 600,
                                display: 'flex',
                                alignItems: 'center',
                                gap: '4px',
                              }}>
                                <span>⚕</span>
                              </div>
                            )}
                            <div style={{ marginLeft: 'auto' }}>
                              {snp.riskLevel && (
                                <div style={{
                                  backgroundColor: getRiskBucket(snp.riskLevel).backgroundColor,
                                  color: getRiskBucket(snp.riskLevel).color,
                                  padding: '4px 10px',
                                  borderRadius: '4px',
                                  fontSize: '14px',
                                  fontWeight: 600,
                                  whiteSpace: 'nowrap',
                                }}>
                                  {getRiskBucket(snp.riskLevel).label}
                                </div>
                              )}
                            </div>
                          </div>

                          {/* Trait Description */}
                          {snp.trait && (
                            <div style={{
                              fontSize: '14px',
                              lineHeight: '1.5',
                              marginBottom: '6px',
                              color: '#333',
                            }}>
                              {snp.trait}
                            </div>
                          )}

                          {/* Risk Information */}
                          {(snp.oddsRatio != null || snp.riskAlleleFrequency != null) && (
                            <div style={{ fontSize: '13px', marginBottom: '6px', color: '#555' }}>
                              {snp.oddsRatio != null && (
                                <div style={{ marginBottom: '2px' }}>
                                  {snp.oddsRatio > 1
                                    ? `${((snp.oddsRatio - 1) * 100).toFixed(0)}% increased risk (OR: ${snp.oddsRatio.toFixed(2)})`
                                    : `${((1 - snp.oddsRatio) * 100).toFixed(0)}% decreased risk (OR: ${snp.oddsRatio.toFixed(2)})`
                                  }
                                </div>
                              )}
                              {snp.riskAlleleFrequency != null && (
                                <div style={{ fontSize: '12px', color: '#666' }}>
                                  {snp.riskAlleleFrequency > 0.5
                                    ? `${(snp.riskAlleleFrequency * 100).toFixed(1)}% of people have this variant`
                                    : `${(snp.riskAlleleFrequency * 100).toFixed(1)}% of people have this variant (relatively rare)`
                                  }
                                </div>
                              )}
                            </div>
                          )}

                          {/* Study Description */}
                          {snp.studyDescription && (
                            <div style={{
                              fontSize: '12px',
                              color: '#666',
                              marginBottom: '4px',
                              fontStyle: 'italic',
                            }}>
                              Study: {snp.studyDescription}
                            </div>
                          )}

                          {/* Clinical Info */}
                          {snp.clinvarCondition && snp.clinvarCondition !== 'not provided' && (
                            <div style={{
                              fontSize: '13px',
                              color: '#F57F17',
                              fontWeight: 500,
                            }}>
                              Clinical: {snp.clinvarCondition}
                            </div>
                          )}
                        </div>
                      ))}
                    </Stack>

                    {/* Load More Button */}
                    {hasMore && (
                      <div style={{ marginTop: '16px', textAlign: 'center' }}>
                        <button
                          onClick={(): void => { void loadMore(group.genomeAnalysisResultId); }}
                          disabled={loadedData?.isLoading}
                          style={{
                            backgroundColor: loadedData?.isLoading ? '#CCC' : '#007AFF',
                            color: 'white',
                            border: 'none',
                            padding: '10px 24px',
                            borderRadius: '6px',
                            fontSize: '14px',
                            fontWeight: 600,
                            cursor: loadedData?.isLoading ? 'not-allowed' : 'pointer',
                            transition: 'background-color 0.2s',
                          }}
                          onMouseEnter={(e): void => {
                            if (!loadedData?.isLoading) {
                              e.currentTarget.style.backgroundColor = '#0051D5';
                            }
                          }}
                          onMouseLeave={(e): void => {
                            if (!loadedData?.isLoading) {
                              e.currentTarget.style.backgroundColor = '#007AFF';
                            }
                          }}
                        >
                          {loadedData?.isLoading ? 'Loading...' : `Load More (${Math.min(20, group.totalCount - displaySnps.length)} of ${group.totalCount - displaySnps.length} remaining)`}
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </Stack>
      </div>
    </Stack>
  );
}
