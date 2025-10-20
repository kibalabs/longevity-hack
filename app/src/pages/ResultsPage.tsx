import React from 'react';

import { useNavigator } from '@kibalabs/core-react';
import { Alignment, Direction, PaddingSize, Stack, Text } from '@kibalabs/ui-react';

import * as Resources from '../client/resources';
import { useGlobals } from '../GlobalsContext';
import { getRiskBucket, getRiskPriority } from '../util';
import { getCategoryDisplayName } from '../util/categoryNames';

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
  const [expandedSnps, setExpandedSnps] = React.useState<Set<string>>(new Set());
  const [subscribedCategories, setSubscribedCategories] = React.useState<Set<string>>(new Set());
  const [expandedPapers, setExpandedPapers] = React.useState<Map<string, boolean>>(new Map());
  const [categorySnpsData, setCategorySnpsData] = React.useState<Map<string, CategorySnpsData>>(new Map());
  const [categoryAnalyses, setCategoryAnalyses] = React.useState<Map<string, Resources.CategoryAnalysis>>(new Map());
  const [analyzingCategories, setAnalyzingCategories] = React.useState<Set<string>>(new Set());

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

  // Auto-load SNPs when a category is expanded for the first time
  React.useEffect((): void => {
    expandedGroups.forEach((groupId): void => {
      const data = categorySnpsData.get(groupId);
      // If expanded but no data exists yet, and not currently loading, trigger load
      if (data && data.snps.length === 0 && !data.isLoading && data.hasMore) {
        void loadMore(groupId);
      }
    });
  }, [expandedGroups, categorySnpsData]);

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
        // Initialize category data if not already present
        if (!categorySnpsData.has(groupId)) {
          setCategorySnpsData((prevData): Map<string, CategorySnpsData> => {
            const newMap = new Map(prevData);
            newMap.set(groupId, {
              snps: [],
              totalCount: group.totalCount,
              hasMore: group.totalCount > 0,
              isLoading: false,
            });
            return newMap;
          });
        }
      }
      return newSet;
    });
  };

  const toggleSnp = (snpKey: string): void => {
    setExpandedSnps((prev): Set<string> => {
      const newSet = new Set(prev);
      if (newSet.has(snpKey)) {
        newSet.delete(snpKey);
      } else {
        newSet.add(snpKey);
      }
      return newSet;
    });
  };

  const toggleCategorySubscription = (categoryId: string): void => {
    setSubscribedCategories((prev): Set<string> => {
      const newSet = new Set(prev);
      if (newSet.has(categoryId)) {
        newSet.delete(categoryId);
      } else {
        newSet.add(categoryId);
      }
      return newSet;
    });
  };

  const toggleExpandAllPapers = (categoryId: string): void => {
    setExpandedPapers((prev): Map<string, boolean> => {
      const newMap = new Map(prev);
      const currentState = newMap.get(categoryId) || false;
      newMap.set(categoryId, !currentState);
      return newMap;
    });
  };

  const analyzeCategory = async (genomeAnalysisResultId: string): Promise<void> => {
    if (!genomeAnalysisId) return;

    setAnalyzingCategories((prev): Set<string> => new Set(prev).add(genomeAnalysisResultId));
    try {
      const analysis = await longevityClient.analyzeCategory(genomeAnalysisId, genomeAnalysisResultId);
      setCategoryAnalyses((prev): Map<string, Resources.CategoryAnalysis> => {
        const newMap = new Map(prev);
        newMap.set(genomeAnalysisResultId, analysis);
        return newMap;
      });
    } catch (error) {
      console.error('Failed to analyze category:', error);
      alert('Failed to generate AI analysis. Please try again.');
    } finally {
      setAnalyzingCategories((prev): Set<string> => {
        const newSet = new Set(prev);
        newSet.delete(genomeAnalysisResultId);
        return newSet;
      });
    }
  };

  const loadMore = async (genomeAnalysisResultId: string): Promise<void> => {
    if (!genomeAnalysisId) return;

    const currentData = categorySnpsData.get(genomeAnalysisResultId);
    if (!currentData) return;

    // If already loading, don't start another request
    if (currentData.isLoading) return;

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
                      <Text variant='bold'>{getCategoryDisplayName(group.category)}</Text>
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
                      <Text variant='note'>{group.categoryDescription}</Text>
                    </div>
                  )}
                </div>

                {/* Expanded Content */}
                {isExpanded && (
                  <div style={{ padding: '20px', backgroundColor: '#FAFBFC' }}>

                    {/* Two column layout */}
                    <div style={{ display: 'flex', gap: '20px', alignItems: 'flex-start' }}>

                      {/* Left column - AI Analysis + Your Genotypes */}
                      <div style={{ flex: '1', minWidth: '0' }}>

                        {/* AI Analysis Section or Generate Button */}
                        {categoryAnalyses.has(group.genomeAnalysisResultId) ? (
                          <div style={{
                            marginBottom: '20px',
                            padding: '20px',
                            backgroundColor: '#E8F4FD',
                            borderRadius: '8px',
                            border: '1px solid #B3D9FF',
                          }}>
                            <div style={{
                              fontSize: '16px',
                              fontWeight: 600,
                              marginBottom: '12px',
                              color: '#1A73E8',
                              letterSpacing: '-0.2px',
                            }}>
                              AI Interpretation
                            </div>
                            <div style={{
                              fontSize: '13px',
                              color: '#5F6368',
                              marginBottom: '16px',
                            }}>
                              Based on your genetic data and the latest research
                            </div>

                            {/* Analysis content - displayed as-is */}
                            <div style={{
                              fontSize: '14px',
                              lineHeight: '1.6',
                              color: '#3C4043',
                              whiteSpace: 'pre-wrap',
                            }}>
                              {categoryAnalyses.get(group.genomeAnalysisResultId)!.analysis}
                            </div>
                          </div>
                        ) : (
                          <div style={{ marginBottom: '20px' }}>
                            <button
                              onClick={(): void => { void analyzeCategory(group.genomeAnalysisResultId); }}
                              disabled={analyzingCategories.has(group.genomeAnalysisResultId)}
                              style={{
                                width: '100%',
                                padding: '12px 16px',
                                backgroundColor: analyzingCategories.has(group.genomeAnalysisResultId) ? '#DADCE0' : '#1A73E8',
                                color: 'white',
                                border: 'none',
                                borderRadius: '6px',
                                fontSize: '14px',
                                fontWeight: 600,
                                cursor: analyzingCategories.has(group.genomeAnalysisResultId) ? 'not-allowed' : 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: '8px',
                              }}
                            >
                              {analyzingCategories.has(group.genomeAnalysisResultId) ? 'Analyzing...' : 'Generate AI Analysis'}
                            </button>
                          </div>
                        )}

                        {/* Your Genotypes Section */}
                        <div style={{
                          fontSize: '15px',
                          fontWeight: 600,
                          marginBottom: '16px',
                          color: '#202124',
                        }}>
                          Your Genotypes
                        </div>

                        {/* SNP Table */}
                        <div style={{
                          backgroundColor: 'white',
                          border: '1px solid #DADCE0',
                          borderRadius: '8px',
                          overflow: 'hidden',
                        }}>
                          {/* Table Header */}
                          <div style={{
                            display: 'grid',
                            gridTemplateColumns: '100px 120px 120px 140px',
                            gap: '12px',
                            padding: '12px 16px',
                            backgroundColor: '#F8F9FA',
                            borderBottom: '1px solid #DADCE0',
                            fontSize: '12px',
                            fontWeight: 600,
                            color: '#5F6368',
                            textTransform: 'uppercase',
                            letterSpacing: '0.5px',
                          }}>
                            <div>RSID</div>
                            <div>GENOTYPE</div>
                            <div>EFFECT ALLELE</div>
                            <div>RISK LEVEL</div>
                          </div>

                          {/* Table Rows */}
                          {displaySnps.map((snp: Resources.SNP, index: number): React.ReactElement => {
                            const snpKey = `${group.genomeAnalysisResultId}-${snp.rsid}-${index}`;
                            const isSnpExpanded = expandedSnps.has(snpKey);

                            return (
                              <div key={snpKey}>
                                {/* Row Header - Clickable */}
                                <div
                                  onClick={(): void => toggleSnp(snpKey)}
                                  style={{
                                    display: 'grid',
                                    gridTemplateColumns: '100px 120px 120px 140px',
                                    gap: '12px',
                                    padding: '16px',
                                    borderBottom: '1px solid #DADCE0',
                                    cursor: 'pointer',
                                    transition: 'background-color 0.15s',
                                  }}
                                  onMouseEnter={(e): void => { e.currentTarget.style.backgroundColor = '#F8F9FA'; }}
                                  onMouseLeave={(e): void => { e.currentTarget.style.backgroundColor = 'white'; }}
                                >
                                  <div style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '6px',
                                  }}>
                                    <span style={{ fontSize: '11px', color: '#5F6368' }}>{isSnpExpanded ? '▼' : '▶'}</span>
                                    <div style={{
                                      color: '#1A73E8',
                                      fontSize: '14px',
                                      fontWeight: 500,
                                    }}>
                                      {snp.rsid}
                                    </div>
                                  </div>
                                  <div style={{
                                    fontSize: '14px',
                                    color: '#202124',
                                    fontWeight: 500,
                                  }}>
                                    {snp.genotype}
                                  </div>
                                  <div style={{
                                    fontSize: '14px',
                                    color: '#202124',
                                  }}>
                                    {snp.riskAllele || '-'}
                                  </div>
                                  <div>
                                    {snp.riskLevel && (
                                      <div style={{
                                        backgroundColor: getRiskBucket(snp.riskLevel).backgroundColor,
                                        color: getRiskBucket(snp.riskLevel).color,
                                        padding: '4px 10px',
                                        borderRadius: '12px',
                                        fontSize: '12px',
                                        fontWeight: 600,
                                        display: 'inline-block',
                                        whiteSpace: 'nowrap',
                                      }}>
                                        {getRiskBucket(snp.riskLevel).label}
                                      </div>
                                    )}
                                  </div>
                                </div>

                                {/* Expanded details - still using existing structure */}
                                {isSnpExpanded && (
                                  <div style={{
                                    padding: '16px',
                                    backgroundColor: '#F8F9FA',
                                    borderBottom: '1px solid #DADCE0',
                                  }}>
                                    {snp.trait && (
                                      <div style={{
                                        marginBottom: '12px',
                                        fontSize: '14px',
                                        color: '#202124',
                                        lineHeight: '1.5',
                                      }}>
                                        {snp.trait}
                                      </div>
                                    )}
                                    {(snp.oddsRatio != null || snp.riskAlleleFrequency != null || snp.pValue) && (
                                      <div style={{ fontSize: '13px', color: '#5F6368', marginBottom: '8px' }}>
                                        {snp.oddsRatio != null && (
                                          <div style={{ marginBottom: '4px' }}>
                                            Odds Ratio: {snp.oddsRatio.toFixed(2)} {snp.oddsRatio > 1
                                              ? `(${((snp.oddsRatio - 1) * 100).toFixed(0)}% increased risk)`
                                              : snp.oddsRatio < 1 ? `(${((1 - snp.oddsRatio) * 100).toFixed(0)}% decreased risk)` : ''}
                                          </div>
                                        )}
                                        {snp.riskAlleleFrequency != null && (
                                          <div style={{ marginBottom: '4px' }}>
                                            Population frequency: {(snp.riskAlleleFrequency * 100).toFixed(1)}%
                                          </div>
                                        )}
                                        {snp.pValue && (
                                          <div>P-value: {snp.pValue}</div>
                                        )}
                                      </div>
                                    )}
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>

                        {/* Load More Button */}
                        {hasMore && (
                          <div style={{ marginTop: '16px' }}>
                            <button
                              onClick={(): void => { void loadMore(group.genomeAnalysisResultId); }}
                              disabled={loadedData?.isLoading}
                              style={{
                                width: '100%',
                                backgroundColor: 'white',
                                color: '#1A73E8',
                                border: '1px solid #DADCE0',
                                padding: '10px 16px',
                                borderRadius: '6px',
                                fontSize: '14px',
                                fontWeight: 500,
                                cursor: loadedData?.isLoading ? 'not-allowed' : 'pointer',
                                transition: 'all 0.2s',
                              }}
                              onMouseEnter={(e): void => {
                                if (!loadedData?.isLoading) {
                                  e.currentTarget.style.backgroundColor = '#F8F9FA';
                                }
                              }}
                              onMouseLeave={(e): void => {
                                if (!loadedData?.isLoading) {
                                  e.currentTarget.style.backgroundColor = 'white';
                                }
                              }}
                            >
                              {loadedData?.isLoading ? 'Loading...' : `Load More (${loadedData ? loadedData.totalCount - displaySnps.length : 0} remaining)`}
                            </button>
                          </div>
                        )}
                      </div>

                      {/* Right column - Evidence & Notification */}
                      <div style={{ width: '320px', flexShrink: 0 }}>
                        {/* Evidence Section */}
                        {categoryAnalyses.has(group.genomeAnalysisResultId) && categoryAnalyses.get(group.genomeAnalysisResultId)!.papersUsed.length > 0 && (
                          <div style={{ marginBottom: '20px' }}>
                            <div style={{
                              backgroundColor: 'white',
                              border: '1px solid #DADCE0',
                              borderRadius: '8px',
                              overflow: 'hidden',
                            }}>
                              {/* Title and Expand All inside the card */}
                              <div style={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                padding: '16px',
                                borderBottom: '1px solid #DADCE0',
                              }}>
                                <div style={{
                                  fontSize: '15px',
                                  fontWeight: 600,
                                  color: '#202124',
                                }}>
                                  Evidence
                                </div>
                                <a
                                  href="#"
                                  onClick={(e): void => {
                                    e.preventDefault();
                                    toggleExpandAllPapers(group.genomeAnalysisResultId);
                                  }}
                                  style={{
                                    fontSize: '13px',
                                    color: '#1A73E8',
                                    textDecoration: 'none',
                                    fontWeight: 500,
                                    cursor: 'pointer',
                                  }}
                                >
                                  {expandedPapers.get(group.genomeAnalysisResultId) ? 'Collapse all ↑' : 'Expand all ↓'}
                                </a>
                              </div>

                              {/* Paper list */}
                              {categoryAnalyses.get(group.genomeAnalysisResultId)!.papersUsed.slice(0, 5).map((paper: Resources.PaperReference, index: number): React.ReactElement => {
                                const firstAuthor = paper.authors?.split(',')[0]?.trim() || '';
                                const authorDisplay = firstAuthor ? `${firstAuthor} et al.` : '';
                                const isExpanded = expandedPapers.get(group.genomeAnalysisResultId) || false;
                                const abstractText = paper.abstract || '';
                                const shortAbstract = abstractText.length > 150 ? abstractText.substring(0, 150) + '...' : abstractText;

                                return (
                                  <div
                                    key={paper.pubmedId}
                                    style={{
                                      padding: '12px 16px',
                                      borderBottom: index < Math.min(4, categoryAnalyses.get(group.genomeAnalysisResultId)!.papersUsed.length - 1) ? '1px solid #DADCE0' : 'none',
                                    }}
                                  >
                                    <div style={{
                                      display: 'flex',
                                      alignItems: 'flex-start',
                                      gap: '8px',
                                      marginBottom: '6px',
                                    }}>
                                      <div style={{
                                        width: '20px',
                                        height: '20px',
                                        backgroundColor: '#E8F0FE',
                                        borderRadius: '50%',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        fontSize: '11px',
                                        fontWeight: 600,
                                        color: '#1A73E8',
                                        flexShrink: 0,
                                      }}>
                                        {String.fromCharCode(78 + index)}
                                      </div>
                                      <div style={{ flex: 1, minWidth: 0 }}>
                                        <div style={{
                                          fontSize: '13px',
                                          fontWeight: 500,
                                          color: '#202124',
                                          marginBottom: '4px',
                                          lineHeight: '1.3',
                                        }}>
                                          {authorDisplay} • {paper.year || ''}
                                        </div>
                                        <div style={{
                                          fontSize: '13px',
                                          color: '#5F6368',
                                          lineHeight: '1.4',
                                          marginBottom: '6px',
                                        }}>
                                          {isExpanded ? paper.title : (paper.title && paper.title.length > 80 ? paper.title.substring(0, 80) + '...' : paper.title)}
                                        </div>
                                        {isExpanded && abstractText && (
                                          <div style={{
                                            fontSize: '12px',
                                            color: '#5F6368',
                                            lineHeight: '1.5',
                                            marginBottom: '8px',
                                            fontStyle: 'italic',
                                          }}>
                                            {abstractText}
                                          </div>
                                        )}
                                        <div style={{ display: 'flex', gap: '12px', fontSize: '12px' }}>
                                          <a
                                            href={`https://pubmed.ncbi.nlm.nih.gov/${paper.pubmedId}/`}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            style={{
                                              color: '#1A73E8',
                                              textDecoration: 'none',
                                              fontWeight: 500,
                                            }}
                                          >
                                            Read ↗
                                          </a>
                                        </div>
                                      </div>
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        )}

                        {/* Notification Settings Section */}
                        <div style={{
                          backgroundColor: 'white',
                          border: '1px solid #DADCE0',
                          borderRadius: '8px',
                          padding: '16px',
                        }}>
                          <div style={{
                            fontSize: '15px',
                            fontWeight: 600,
                            marginBottom: '16px',
                            color: '#202124',
                          }}>
                            Notification Settings
                          </div>

                          <div style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            marginBottom: '12px',
                          }}>
                            <div style={{ fontSize: '14px', color: '#202124' }}>
                              Follow updates
                            </div>
                            <div
                              onClick={(): void => toggleCategorySubscription(group.genomeAnalysisResultId)}
                              style={{
                                width: '44px',
                                height: '24px',
                                backgroundColor: subscribedCategories.has(group.genomeAnalysisResultId) ? '#1A73E8' : '#DADCE0',
                                borderRadius: '12px',
                                position: 'relative',
                                cursor: 'pointer',
                                transition: 'background-color 0.2s',
                              }}
                            >
                              <div style={{
                                width: '20px',
                                height: '20px',
                                backgroundColor: 'white',
                                borderRadius: '50%',
                                position: 'absolute',
                                top: '2px',
                                left: subscribedCategories.has(group.genomeAnalysisResultId) ? '22px' : '2px',
                                transition: 'left 0.2s',
                                boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
                              }}></div>
                            </div>
                          </div>

                          <a
                            href="#"
                            style={{
                              fontSize: '13px',
                              color: '#1A73E8',
                              textDecoration: 'none',
                              fontWeight: 500,
                            }}
                          >
                            Advanced notification settings
                          </a>
                        </div>

                        {/* Ask the AI button */}
                        <div style={{ marginTop: '16px' }}>
                          <div style={{
                            backgroundColor: 'white',
                            border: '1px solid #DADCE0',
                            borderRadius: '8px',
                            padding: '16px',
                          }}>
                            <div style={{
                              fontSize: '14px',
                              fontWeight: 600,
                              marginBottom: '8px',
                              color: '#202124',
                            }}>
                              Have questions?
                            </div>
                            <div style={{
                              fontSize: '13px',
                              color: '#5F6368',
                              marginBottom: '12px',
                              lineHeight: '1.4',
                            }}>
                              Ask the AI to explain this trait in simpler terms or dive deeper into the research
                            </div>
                            <button
                              style={{
                                width: '100%',
                                padding: '10px 16px',
                                backgroundColor: '#1A73E8',
                                color: 'white',
                                border: 'none',
                                borderRadius: '6px',
                                fontSize: '14px',
                                fontWeight: 600,
                                cursor: 'pointer',
                              }}
                            >
                              Ask the AI
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
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
