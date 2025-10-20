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
                  <div style={{ padding: '16px' }}>
                    <div style={{ marginBottom: '12px' }}>
                      <Text variant='note'>{group.categoryDescription}</Text>
                    </div>

                    {/* Action buttons row */}
                    <div style={{ marginBottom: '16px', display: 'flex', gap: '12px', alignItems: 'center' }}>
                      {!categoryAnalyses.has(group.genomeAnalysisResultId) && (
                        <button
                          onClick={(): void => { void analyzeCategory(group.genomeAnalysisResultId); }}
                          disabled={analyzingCategories.has(group.genomeAnalysisResultId)}
                          style={{
                            padding: '8px 16px',
                            backgroundColor: analyzingCategories.has(group.genomeAnalysisResultId) ? '#CCCCCC' : '#007AFF',
                            color: 'white',
                            border: 'none',
                            borderRadius: '6px',
                            fontSize: '14px',
                            fontWeight: 600,
                            cursor: analyzingCategories.has(group.genomeAnalysisResultId) ? 'not-allowed' : 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '6px',
                          }}
                        >
                          {analyzingCategories.has(group.genomeAnalysisResultId) ? '⏳ Analyzing...' : '🤖 Analyze with AI'}
                        </button>
                      )}
                      
                      {/* Keep me updated button */}
                      <div 
                        onClick={(): void => toggleCategorySubscription(group.genomeAnalysisResultId)}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '8px',
                          padding: '8px 12px',
                          backgroundColor: '#F8F9FA',
                          borderRadius: '6px',
                          cursor: 'pointer',
                          transition: 'background-color 0.2s',
                          border: '1px solid #E8EAED',
                        }}
                        onMouseEnter={(e): void => { e.currentTarget.style.backgroundColor = '#EEEFF1'; }}
                        onMouseLeave={(e): void => { e.currentTarget.style.backgroundColor = '#F8F9FA'; }}
                      >
                        <div style={{
                          width: '16px',
                          height: '16px',
                          border: '2px solid #5F6368',
                          borderRadius: '3px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          backgroundColor: subscribedCategories.has(group.genomeAnalysisResultId) ? '#007AFF' : 'white',
                          borderColor: subscribedCategories.has(group.genomeAnalysisResultId) ? '#007AFF' : '#5F6368',
                        }}>
                          {subscribedCategories.has(group.genomeAnalysisResultId) && (
                            <div style={{ color: 'white', fontSize: '12px', fontWeight: 'bold' }}>✓</div>
                          )}
                        </div>
                        <div style={{ fontSize: '13px', color: '#5F6368', fontWeight: 500 }}>
                          Keep me updated on the latest research for this category
                        </div>
                      </div>
                    </div>

                    {/* AI Analysis Section */}
                    {categoryAnalyses.has(group.genomeAnalysisResultId) && (
                      <div style={{
                        marginBottom: '16px',
                        padding: '16px',
                        backgroundColor: '#F0F8FF',
                        borderRadius: '8px',
                        border: '1px solid #B3D9FF',
                      }}>
                        <div style={{ fontSize: '16px', fontWeight: 'bold', marginBottom: '12px', color: '#0066CC' }}>
                          🤖 AI Analysis
                        </div>
                        <div style={{ marginBottom: '16px', fontSize: '15px', lineHeight: '1.6', color: '#333' }}>
                          {categoryAnalyses.get(group.genomeAnalysisResultId)!.analysis.split('\n\n').map((para, idx) => (
                            <p key={idx} style={{ margin: '8px 0' }}>{para}</p>
                          ))}
                        </div>
                        {categoryAnalyses.get(group.genomeAnalysisResultId)!.papersUsed.length > 0 && (
                          <div>
                            <div style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '8px', color: '#0066CC' }}>
                              📚 Research Papers ({categoryAnalyses.get(group.genomeAnalysisResultId)!.papersUsed.length})
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                              {categoryAnalyses.get(group.genomeAnalysisResultId)!.papersUsed.map((paper: Resources.PaperReference, index: number): React.ReactElement => {
                                const firstAuthor = paper.authors?.split(',')[0]?.trim() || '';
                                const authorDisplay = firstAuthor ? `${firstAuthor} et al.` : '';
                                const abstractPreview = paper.abstract ? paper.abstract.substring(0, 150) + '...' : '';

                                return (
                                  <div
                                    key={paper.pubmedId}
                                    style={{
                                      padding: '10px',
                                      backgroundColor: 'white',
                                      borderRadius: '6px',
                                      border: '1px solid #D0E8FF',
                                    }}
                                  >
                                    <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '4px', color: '#333' }}>
                                      {index + 1}. {paper.title || 'Untitled'}
                                    </div>
                                    {authorDisplay && (
                                      <div style={{ fontSize: '12px', color: '#666', marginBottom: '2px' }}>
                                        {authorDisplay} • {paper.journal && paper.year ? `${paper.journal}, ${paper.year}` : (paper.year || '')}
                                      </div>
                                    )}
                                    {abstractPreview && (
                                      <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px', lineHeight: '1.4' }}>
                                        {abstractPreview}
                                      </div>
                                    )}
                                    <a
                                      href={`https://pubmed.ncbi.nlm.nih.gov/${paper.pubmedId}/`}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      style={{
                                        fontSize: '12px',
                                        color: '#007AFF',
                                        textDecoration: 'none',
                                      }}
                                    >
                                      PubMed: {paper.pubmedId} →
                                    </a>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    <Stack direction={Direction.Vertical} shouldAddGutters={true} defaultGutter={PaddingSize.Default}>
                      {displaySnps.map((snp: Resources.SNP, index: number): React.ReactElement => {
                        const snpKey = `${group.genomeAnalysisResultId}-${snp.rsid}-${index}`;
                        const isSnpExpanded = expandedSnps.has(snpKey);
                        
                        return (
                          <div
                            key={snpKey}
                            style={{
                              backgroundColor: 'white',
                              borderRadius: '6px',
                              border: '1px solid #E8EAED',
                              overflow: 'hidden',
                            }}
                          >
                            {/* Collapsed SNP Header */}
                            <div
                              onClick={(): void => toggleSnp(snpKey)}
                              style={{
                                padding: '12px',
                                cursor: 'pointer',
                                transition: 'background-color 0.2s',
                              }}
                              onMouseEnter={(e): void => { e.currentTarget.style.backgroundColor = '#F8F9FA'; }}
                              onMouseLeave={(e): void => { e.currentTarget.style.backgroundColor = 'white'; }}
                            >
                              {/* Top Row: rsid, genotype, and badges */}
                              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                  <Text variant='note'>{isSnpExpanded ? '▼' : '▶'}</Text>
                                  <div style={{
                                    color: '#007AFF',
                                    fontWeight: 600,
                                    fontSize: '15px',
                                  }}>
                                    {snp.rsid}
                                  </div>
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
                                {snp.riskAllele && (
                                  <div style={{
                                    backgroundColor: '#E3F2FD',
                                    color: '#1976D2',
                                    padding: '4px 8px',
                                    borderRadius: '4px',
                                    fontSize: '12px',
                                    fontWeight: 500,
                                  }}>
                                    {snp.riskAllele}
                                  </div>
                                )}
                                {snp.effectStrength && (
                                  <div style={{
                                    backgroundColor: snp.effectStrength.toLowerCase() === 'large' ? '#FFEBEE' : '#FFF3E0',
                                    color: snp.effectStrength.toLowerCase() === 'large' ? '#C62828' : '#E65100',
                                    padding: '4px 8px',
                                    borderRadius: '12px',
                                    fontSize: '11px',
                                    fontWeight: 600,
                                    textTransform: 'lowercase',
                                  }}>
                                    {snp.effectStrength}
                                  </div>
                                )}
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

                              {/* Trait Description - always visible */}
                              {snp.trait && (
                                <div style={{
                                  fontSize: '14px',
                                  lineHeight: '1.5',
                                  color: '#333',
                                }}>
                                  {snp.trait}
                                </div>
                              )}
                            </div>

                            {/* Expanded SNP Details */}
                            {isSnpExpanded && (
                              <div style={{ 
                                padding: '0 12px 12px 12px',
                                borderTop: '1px solid #E8EAED',
                              }}>
                                {/* At a glance Section */}
                                <div style={{ marginTop: '12px', marginBottom: '16px' }}>
                                  <div style={{ 
                                    fontSize: '14px', 
                                    fontWeight: 600, 
                                    marginBottom: '8px',
                                    color: '#5F6368',
                                  }}>
                                    At a glance
                                  </div>
                                  <div style={{ 
                                    fontSize: '14px', 
                                    lineHeight: '1.6',
                                    color: '#333',
                                    marginBottom: '8px',
                                  }}>
                                    {snp.trait ? (
                                      <>
                                        The <strong>{snp.riskAllele || 'variant'}</strong> allele at {snp.rsid} contributes to{' '}
                                        {snp.trait.toLowerCase()}.
                                        {snp.oddsRatio && snp.oddsRatio !== 1 && (
                                          <> {snp.oddsRatio > 1 
                                            ? `Studies show ${((snp.oddsRatio - 1) * 100).toFixed(0)}% increased association` 
                                            : `Studies show ${((1 - snp.oddsRatio) * 100).toFixed(0)}% decreased association`
                                          } (OR: {snp.oddsRatio.toFixed(2)}).</>
                                        )}
                                      </>
                                    ) : (
                                      `This variant at ${snp.rsid} has been identified in genetic studies.`
                                    )}
                                  </div>
                                  {snp.riskAlleleFrequency != null && (
                                    <div style={{ 
                                      fontSize: '13px', 
                                      color: '#5F6368',
                                      marginBottom: '8px',
                                    }}>
                                      Population frequency: {(snp.riskAlleleFrequency * 100).toFixed(1)}% of people carry this variant
                                      {snp.riskAlleleFrequency < 0.1 && ' (relatively rare)'}
                                      {snp.riskAlleleFrequency > 0.5 && ' (common variant)'}
                                    </div>
                                  )}
                                  {snp.pValue && (
                                    <div style={{ 
                                      fontSize: '12px', 
                                      color: '#5F6368',
                                      fontFamily: 'monospace',
                                    }}>
                                      P-value: {snp.pValue}
                                    </div>
                                  )}
                                </div>

                                {/* What to watch Section */}
                                {snp.trait && (
                                  <div style={{ marginBottom: '16px' }}>
                                    <div style={{ 
                                      fontSize: '14px', 
                                      fontWeight: 600, 
                                      marginBottom: '8px',
                                      color: '#5F6368',
                                    }}>
                                      What to watch
                                    </div>
                                    <div style={{ 
                                      fontSize: '14px', 
                                      lineHeight: '1.6',
                                      color: '#333',
                                    }}>
                                      {group.category === 'Cardiological' && (
                                        <>Monitor cardiovascular health markers. Consider regular check-ups and maintaining a heart-healthy lifestyle.</>
                                      )}
                                      {group.category === 'T2D' && (
                                        <>Keep track of blood glucose levels and maintain a balanced diet. Regular exercise can help manage risk.</>
                                      )}
                                      {group.category !== 'Cardiological' && group.category !== 'T2D' && (
                                        <>Stay informed about {snp.trait.toLowerCase()}. Discuss with healthcare provider for personalized guidance.</>
                                      )}
                                    </div>
                                  </div>
                                )}

                                {/* Evidence Section */}
                                {snp.studyDescription && (
                                  <div style={{ marginBottom: '16px' }}>
                                    <div style={{ 
                                      fontSize: '14px', 
                                      fontWeight: 600, 
                                      marginBottom: '8px',
                                      color: '#5F6368',
                                    }}>
                                      Evidence
                                    </div>
                                    <div style={{
                                      backgroundColor: '#F8F9FA',
                                      padding: '12px',
                                      borderRadius: '6px',
                                      marginBottom: '8px',
                                    }}>
                                      <div style={{ 
                                        fontSize: '13px',
                                        fontWeight: 500,
                                        marginBottom: '4px',
                                        color: '#333',
                                      }}>
                                        {snp.trait || 'Genetic association study'}
                                      </div>
                                      <div style={{ 
                                        fontSize: '13px',
                                        color: '#5F6368',
                                        marginBottom: '8px',
                                        lineHeight: '1.5',
                                      }}>
                                        {snp.studyDescription}
                                      </div>
                                      {snp.sources && snp.sources.length > 0 && (
                                        <div style={{ fontSize: '12px', color: '#1976D2' }}>
                                          {snp.sources.includes('gwas_catalog') && (
                                            <a
                                              href={`https://www.ebi.ac.uk/gwas/search?query=${snp.rsid}`}
                                              target="_blank"
                                              rel="noopener noreferrer"
                                              style={{ color: '#007AFF', textDecoration: 'none', marginRight: '12px' }}
                                            >
                                              GWAS Catalog ↗
                                            </a>
                                          )}
                                          <a
                                            href={`https://www.ncbi.nlm.nih.gov/snp/${snp.rsid}`}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            style={{ color: '#007AFF', textDecoration: 'none' }}
                                          >
                                            dbSNP ↗
                                          </a>
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                )}

                                {/* Clinical Info */}
                                {snp.clinvarCondition && snp.clinvarCondition !== 'not provided' && (
                                  <div style={{
                                    backgroundColor: '#FFF9C4',
                                    padding: '12px',
                                    borderRadius: '6px',
                                    marginBottom: '12px',
                                  }}>
                                    <div style={{
                                      fontSize: '13px',
                                      fontWeight: 600,
                                      color: '#F57F17',
                                      marginBottom: '4px',
                                    }}>
                                      ⚕️ Clinical Significance
                                    </div>
                                    <div style={{
                                      fontSize: '13px',
                                      color: '#5F6368',
                                    }}>
                                      {snp.clinvarCondition}
                                    </div>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        );
                      })}
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
                          {loadedData?.isLoading ? 'Loading...' : `Load More`}
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
