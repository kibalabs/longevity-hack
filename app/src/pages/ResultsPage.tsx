import React from 'react';

import { useNavigator } from '@kibalabs/core-react';
import { Alignment, Direction, PaddingSize, Stack, Text } from '@kibalabs/ui-react';

import * as Resources from '../client/resources';
import { ChatModal } from '../components/ChatModal';
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
  const [showSubscriptionPopup, setShowSubscriptionPopup] = React.useState<boolean>(false);
  const [showSubscriptionSuccess, setShowSubscriptionSuccess] = React.useState<boolean>(false);
  const [userEmail, setUserEmail] = React.useState<string>('');
  const [hasSubmittedEmail, setHasSubmittedEmail] = React.useState<boolean>(false);
  const [chatModalOpen, setChatModalOpen] = React.useState<boolean>(false);
  const [activeChatCategory, setActiveChatCategory] = React.useState<{ id: string; name: string; description: string } | null>(null);

  // Load subscriptions and check if email was submitted on mount
  React.useEffect((): void => {
    const storedSubscriptions = localStorage.getItem('notificationSubscriptions');
    if (storedSubscriptions) {
      try {
        const parsed = JSON.parse(storedSubscriptions);
        setSubscribedCategories(new Set(parsed));
      } catch (error) {
        console.error('Failed to parse stored subscriptions:', error);
      }
    }

    // Check if user has already submitted their email
    const storedEmail = localStorage.getItem('subscriptionInterestEmail');
    if (storedEmail) {
      setHasSubmittedEmail(true);
    }
  }, []);

  // Save subscriptions to localStorage whenever they change
  React.useEffect((): void => {
    localStorage.setItem('notificationSubscriptions', JSON.stringify(Array.from(subscribedCategories)));
  }, [subscribedCategories]);

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
        // Unsubscribing - just remove it
        newSet.delete(categoryId);
      } else {
        // Subscribing - check if they already have 1 subscription
        if (newSet.size >= 1) {
          // Show popup for paid subscription
          setShowSubscriptionPopup(true);
          return prev; // Don't add yet
        }
        newSet.add(categoryId);
      }
      return newSet;
    });
  };

  const handleSubscriptionSubmit = async (): Promise<void> => {
    if (!userEmail || !userEmail.includes('@')) {
      alert('Please enter a valid email address');
      return;
    }

    try {
      // Send subscription to API
      await longevityClient.subscribeToNotifications(userEmail);

      // Store email in localStorage for future reference
      localStorage.setItem('subscriptionInterestEmail', userEmail);
      setHasSubmittedEmail(true);

      // Show success view
      setShowSubscriptionPopup(false);
      setShowSubscriptionSuccess(true);
    } catch (error) {
      console.error('Failed to subscribe:', error);
      alert('Failed to submit subscription. Please try again.');
    }
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

  const handleOpenChat = (categoryId: string, categoryName: string, categoryDescription: string): void => {
    setActiveChatCategory({ id: categoryId, name: categoryName, description: categoryDescription });
    setChatModalOpen(true);
  };

  const handleSendChatMessage = async (message: string): Promise<string> => {
    if (!genomeAnalysisId || !activeChatCategory) {
      throw new Error('No active chat category');
    }
    
    const response = await longevityClient.chatWithAgent(genomeAnalysisId, activeChatCategory.id, message);
    return response;
  };

  if (!overview) {
    return (
      <Stack direction={Direction.Vertical} isFullWidth={true} isFullHeight={true} childAlignment={Alignment.Center} contentAlignment={Alignment.Center}>
        <Text variant='default'>Loading results...</Text>
      </Stack>
    );
  }

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      overflow: 'hidden',
    }}>
      {/* Compact Header with glassmorphism */}
        <div style={{
          borderBottom: '1px solid rgba(255, 255, 255, 0.2)',
          background: 'linear-gradient(135deg, rgba(255, 250, 255, 0.9) 0%, rgba(255, 245, 250, 0.9) 100%)',
          backdropFilter: 'blur(20px)',
          boxShadow: '0 4px 16px rgba(102, 126, 234, 0.1)',
        }}>
          <div style={{
            maxWidth: '1200px',
            margin: '0 auto',
            padding: '20px 32px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}>
            {/* Logo on the left */}
            <div style={{
              fontSize: '20px',
              fontWeight: 700,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}>
              GenomeAgent
            </div>

            {/* Stats on the right */}
            {overview.summary && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
                <div style={{ fontSize: '13px', color: '#666' }}>
                  <span style={{ fontWeight: 600, color: '#667eea' }}>{overview.summary.matchedSnps?.toLocaleString()}</span> associations
                </div>
                <div style={{ fontSize: '13px', color: '#666' }}>
                  <span style={{ fontWeight: 600, color: '#667eea' }}>{overview.categoryGroups.length}</span> categories
                </div>
                {overview.summary.clinvarCount && overview.summary.clinvarCount > 0 && (
                  <div style={{ fontSize: '13px', color: '#666' }}>
                    ⚕️ <span style={{ fontWeight: 600, color: '#667eea' }}>{overview.summary.clinvarCount}</span> clinical
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Scrollable Content */}
        <div style={{ flex: 1, overflowY: 'auto', overflowX: 'hidden' }}>
          <div style={{
            width: '100%',
            maxWidth: '1200px',
            margin: '0 auto',
            padding: '0 24px 80px 24px',
          }}>
            {/* Page Header */}
            <div style={{
              padding: '48px 0 40px 0',
              textAlign: 'center',
            }}>
              <style>{`
                @keyframes gradientShift {
                  0% {
                    background-position: 0% 50%;
                  }
                  50% {
                    background-position: 100% 50%;
                  }
                  100% {
                    background-position: 0% 50%;
                  }
                }
              `}</style>
              <h1 style={{
                fontSize: '42px',
                fontWeight: 700,
                margin: '0 0 16px 0',
                letterSpacing: '-0.5px',
                lineHeight: '1.2',
                paddingBottom: '8px',
                background: 'linear-gradient(90deg, #667eea 0%, #764ba2 25%, #f093fb 50%, #667eea 75%, #764ba2 100%)',
                backgroundSize: '200% auto',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
                animation: 'gradientShift 8s ease-in-out infinite',
                display: 'inline-block',
              }}>
                Your Genome Results
              </h1>
              <p style={{
                fontSize: '16px',
                color: '#444',
                lineHeight: '1.6',
                maxWidth: '700px',
                margin: '0 auto',
                fontWeight: 500,
              }}>
                We've analyzed your genetic data and organized the findings into key health categories.
                These insights focus on the most impactful markers for longevity and healthspan,
                helping you understand your unique genetic profile.
              </p>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {overview.categoryGroups.map((group: Resources.GenomeAnalysisCategoryGroup): React.ReactElement => {
            const isExpanded = expandedGroups.has(group.genomeAnalysisResultId);
            const loadedData = categorySnpsData.get(group.genomeAnalysisResultId);
            const displaySnps = loadedData ? loadedData.snps : group.topSnps;
            const hasMore = loadedData ? loadedData.hasMore : group.totalCount > 5;

            return (
              <div
                key={group.genomeAnalysisResultId}
                style={{
                  border: '1px solid rgba(255, 255, 255, 0.4)',
                  borderRadius: '20px',
                  background: 'linear-gradient(135deg, rgba(255, 250, 255, 0.85) 0%, rgba(255, 245, 250, 0.85) 100%)',
                  backdropFilter: 'blur(20px)',
                  overflow: 'hidden',
                  boxShadow: '0 8px 32px rgba(102, 126, 234, 0.12), 0 2px 8px rgba(0, 0, 0, 0.04)',
                  transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
                  width: '100%',
                }}
                onMouseEnter={(e): void => {
                  if (!isExpanded) {
                    e.currentTarget.style.boxShadow = '0 12px 48px rgba(102, 126, 234, 0.2), 0 4px 12px rgba(0, 0, 0, 0.08)';
                    e.currentTarget.style.transform = 'translateY(-4px) scale(1.01)';
                  }
                }}
                onMouseLeave={(e): void => {
                  e.currentTarget.style.boxShadow = '0 8px 32px rgba(102, 126, 234, 0.12), 0 2px 8px rgba(0, 0, 0, 0.04)';
                  e.currentTarget.style.transform = 'translateY(0) scale(1)';
                }}
              >
                {/* Group Header - Clickable */}
                <div
                  onClick={(): void => toggleGroup(group.genomeAnalysisResultId, group)}
                  style={{
                    padding: '24px 28px',
                    background: isExpanded
                      ? 'linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%)'
                      : 'transparent',
                    cursor: 'pointer',
                    borderBottom: isExpanded ? '1px solid rgba(102, 126, 234, 0.2)' : 'none',
                    transition: 'background 0.3s ease',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flex: 1 }}>
                      <div style={{
                        width: '48px',
                        height: '48px',
                        borderRadius: '14px',
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '24px',
                        boxShadow: '0 4px 12px rgba(102, 126, 234, 0.3)',
                      }}>
                        🧬
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{
                          fontSize: '20px',
                          fontWeight: 700,
                          color: '#1a1a1a',
                        }}>
                          {getCategoryDisplayName(group.category)}
                        </div>
                      </div>
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        background: 'rgba(102, 126, 234, 0.1)',
                        padding: '8px 16px',
                        borderRadius: '12px',
                      }}>
                        {group.riskCounts.very_high > 0 && (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <span style={{ fontSize: '16px' }}>🔴</span>
                            <span style={{ fontSize: '13px', fontWeight: 600, color: '#dc2626' }}>{group.riskCounts.very_high}</span>
                          </div>
                        )}
                        {group.riskCounts.high > 0 && (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <span style={{ fontSize: '16px' }}>🟠</span>
                            <span style={{ fontSize: '13px', fontWeight: 600, color: '#ea580c' }}>{group.riskCounts.high}</span>
                          </div>
                        )}
                        {group.riskCounts.moderate > 0 && (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <span style={{ fontSize: '16px' }}>🟡</span>
                            <span style={{ fontSize: '13px', fontWeight: 600, color: '#ca8a04' }}>{group.riskCounts.moderate}</span>
                          </div>
                        )}
                        {group.riskCounts.slight > 0 && (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <span style={{ fontSize: '16px' }}>🔵</span>
                            <span style={{ fontSize: '13px', fontWeight: 600, color: '#2563eb' }}>{group.riskCounts.slight}</span>
                          </div>
                        )}
                        {group.riskCounts.lower > 0 && (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <span style={{ fontSize: '16px' }}>🟢</span>
                            <span style={{ fontSize: '13px', fontWeight: 600, color: '#16a34a' }}>{group.riskCounts.lower}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
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
                                padding: '14px 20px',
                                background: analyzingCategories.has(group.genomeAnalysisResultId)
                                  ? 'rgba(0, 0, 0, 0.15)'
                                  : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                color: 'white',
                                border: 'none',
                                borderRadius: '12px',
                                fontSize: '15px',
                                fontWeight: 700,
                                cursor: analyzingCategories.has(group.genomeAnalysisResultId) ? 'not-allowed' : 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: '8px',
                                boxShadow: analyzingCategories.has(group.genomeAnalysisResultId)
                                  ? 'none'
                                  : '0 4px 16px rgba(102, 126, 234, 0.3)',
                                transition: 'all 0.3s ease',
                              }}
                              onMouseEnter={(e): void => {
                                if (!analyzingCategories.has(group.genomeAnalysisResultId)) {
                                  e.currentTarget.style.transform = 'translateY(-2px)';
                                  e.currentTarget.style.boxShadow = '0 6px 20px rgba(102, 126, 234, 0.4)';
                                }
                              }}
                              onMouseLeave={(e): void => {
                                if (!analyzingCategories.has(group.genomeAnalysisResultId)) {
                                  e.currentTarget.style.transform = 'translateY(0)';
                                  e.currentTarget.style.boxShadow = '0 4px 16px rgba(102, 126, 234, 0.3)';
                                }
                              }}
                            >
                              {analyzingCategories.has(group.genomeAnalysisResultId) ? 'Analyzing...' : 'Request Agent Analysis'}
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
                                background: 'transparent',
                                color: '#667eea',
                                border: '2px solid #667eea',
                                padding: '12px 20px',
                                borderRadius: '12px',
                                fontSize: '15px',
                                fontWeight: 600,
                                cursor: loadedData?.isLoading ? 'not-allowed' : 'pointer',
                                transition: 'all 0.3s ease',
                                opacity: loadedData?.isLoading ? 0.5 : 1,
                              }}
                              onMouseEnter={(e): void => {
                                if (!loadedData?.isLoading) {
                                  e.currentTarget.style.background = 'rgba(102, 126, 234, 0.08)';
                                  e.currentTarget.style.transform = 'translateY(-2px)';
                                }
                              }}
                              onMouseLeave={(e): void => {
                                if (!loadedData?.isLoading) {
                                  e.currentTarget.style.background = 'transparent';
                                  e.currentTarget.style.transform = 'translateY(0)';
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

                          {hasSubmittedEmail ? (
                            // Show confirmation message if email was submitted
                            <div style={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: '12px',
                              padding: '12px',
                              backgroundColor: '#E8F5E9',
                              borderRadius: '6px',
                            }}>
                              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <circle cx="12" cy="12" r="10" fill="#34A853"/>
                                <path d="M9 12.5l2 2 4-4" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                              </svg>
                              <div style={{
                                fontSize: '14px',
                                color: '#1E4620',
                                lineHeight: '1.5',
                              }}>
                                Thanks for your interest! We'll notify you as soon as notifications are ready.
                              </div>
                            </div>
                          ) : (
                            // Show normal toggle if email not submitted
                            <>
                              <div style={{
                                fontSize: '14px',
                                color: '#5F6368',
                                lineHeight: '1.6',
                                marginBottom: '16px',
                              }}>
                                Get a dedicated AI agent that monitors new research related to your {group.category.toLowerCase()} genetics and explains what it means for you.
                              </div>

                              <div style={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                              }}>
                                <div style={{
                                  fontSize: '14px',
                                  color: '#202124',
                                  fontWeight: 500,
                                }}>
                                  Assign AI research agent
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
                            </>
                          )}
                        </div>

                        {/* Ask your agent button */}
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
                              Ask your agent to explain this trait in simpler terms or dive deeper into the research
                            </div>
                            <button
                              onClick={(): void => handleOpenChat(group.genomeAnalysisResultId, getCategoryDisplayName(group.category), group.categoryDescription)}
                              style={{
                                width: '100%',
                                padding: '12px 20px',
                                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                color: 'white',
                                border: 'none',
                                borderRadius: '12px',
                                fontSize: '15px',
                                fontWeight: 700,
                                cursor: 'pointer',
                                boxShadow: '0 4px 16px rgba(102, 126, 234, 0.3)',
                                transition: 'all 0.3s ease',
                              }}
                              onMouseEnter={(e): void => {
                                e.currentTarget.style.transform = 'translateY(-2px)';
                                e.currentTarget.style.boxShadow = '0 6px 20px rgba(102, 126, 234, 0.4)';
                              }}
                              onMouseLeave={(e): void => {
                                e.currentTarget.style.transform = 'translateY(0)';
                                e.currentTarget.style.boxShadow = '0 4px 16px rgba(102, 126, 234, 0.3)';
                              }}
                            >
                              Ask your agent
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
            </div>
          </div>
        </div>

      {/* Subscription Popup Modal */}
      {showSubscriptionPopup && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
        }}
        onClick={(): void => setShowSubscriptionPopup(false)}
        >
          <div
            style={{
              backgroundColor: 'white',
              borderRadius: '12px',
              padding: '32px',
              maxWidth: '480px',
              width: '90%',
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.2)',
            }}
            onClick={(e): void => e.stopPropagation()}
          >
            <div style={{
              fontSize: '24px',
              fontWeight: 600,
              marginBottom: '16px',
              color: '#202124',
            }}>
              AI Research Agents
            </div>

            <div style={{
              fontSize: '15px',
              lineHeight: '1.6',
              color: '#5F6368',
              marginBottom: '24px',
            }}>
              Get dedicated AI agents monitoring new research for up to 10 genetic categories for <strong>$20/year</strong>.
              <br /><br />
              Your agents will continuously scan the latest studies, alert you to relevant findings, and explain what they mean for your specific genetics.
            </div>

            <div style={{
              marginBottom: '24px',
            }}>
              <label style={{
                display: 'block',
                fontSize: '14px',
                fontWeight: 600,
                marginBottom: '8px',
                color: '#202124',
              }}>
                Enter your email to be notified when AI agents launch:
              </label>
              <input
                type="email"
                value={userEmail}
                onChange={(e): void => setUserEmail(e.target.value)}
                placeholder="your.email@example.com"
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '1px solid #DADCE0',
                  borderRadius: '6px',
                  fontSize: '14px',
                  boxSizing: 'border-box',
                }}
                onKeyDown={(e): void => {
                  if (e.key === 'Enter') {
                    handleSubscriptionSubmit();
                  }
                }}
              />
            </div>

            <div style={{
              display: 'flex',
              gap: '12px',
              justifyContent: 'flex-end',
            }}>
              <button
                onClick={(): void => {
                  setShowSubscriptionPopup(false);
                  setUserEmail('');
                }}
                style={{
                  padding: '12px 28px',
                  background: 'transparent',
                  color: '#667eea',
                  border: '2px solid #667eea',
                  borderRadius: '12px',
                  fontSize: '15px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                }}
                onMouseEnter={(e): void => {
                  e.currentTarget.style.background = 'rgba(102, 126, 234, 0.08)';
                }}
                onMouseLeave={(e): void => {
                  e.currentTarget.style.background = 'transparent';
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleSubscriptionSubmit}
                style={{
                  padding: '12px 28px',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '12px',
                  fontSize: '15px',
                  fontWeight: 700,
                  cursor: 'pointer',
                  boxShadow: '0 4px 16px rgba(102, 126, 234, 0.3)',
                  transition: 'all 0.3s ease',
                }}
                onMouseEnter={(e): void => {
                  e.currentTarget.style.transform = 'translateY(-2px)';
                  e.currentTarget.style.boxShadow = '0 6px 20px rgba(102, 126, 234, 0.4)';
                }}
                onMouseLeave={(e): void => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = '0 4px 16px rgba(102, 126, 234, 0.3)';
                }}
              >
                Notify Me
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Subscription Success Modal */}
      {showSubscriptionSuccess && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
        }}
        onClick={(): void => {
          setShowSubscriptionSuccess(false);
          setUserEmail('');
        }}
        >
          <div
            style={{
              backgroundColor: 'white',
              borderRadius: '12px',
              padding: '48px 32px',
              maxWidth: '480px',
              width: '90%',
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.2)',
              textAlign: 'center',
            }}
            onClick={(e): void => e.stopPropagation()}
          >
            {/* Success Icon */}
            <div style={{
              width: '80px',
              height: '80px',
              borderRadius: '50%',
              backgroundColor: '#34A853',
              margin: '0 auto 24px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z" fill="white"/>
              </svg>
            </div>

            <div style={{
              fontSize: '28px',
              fontWeight: 700,
              marginBottom: '16px',
              color: '#202124',
            }}>
              You're all set!
            </div>

            <div style={{
              fontSize: '16px',
              lineHeight: '1.6',
              color: '#5F6368',
              marginBottom: '32px',
            }}>
              You'll be the first to hear when your AI research agents are ready to start monitoring.
            </div>

            <button
              onClick={(): void => {
                setShowSubscriptionSuccess(false);
                setUserEmail('');
              }}
              style={{
                padding: '14px 36px',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                color: 'white',
                border: 'none',
                borderRadius: '12px',
                fontSize: '16px',
                fontWeight: 700,
                cursor: 'pointer',
                boxShadow: '0 4px 16px rgba(102, 126, 234, 0.3)',
                transition: 'all 0.3s ease',
              }}
              onMouseEnter={(e): void => {
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = '0 6px 20px rgba(102, 126, 234, 0.4)';
              }}
              onMouseLeave={(e): void => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = '0 4px 16px rgba(102, 126, 234, 0.3)';
              }}
            >
              Got it
            </button>
          </div>
        </div>
      )}

      {/* Chat Modal */}
      {activeChatCategory && (
        <ChatModal
          isOpen={chatModalOpen}
          onClose={(): void => {
            setChatModalOpen(false);
            setActiveChatCategory(null);
          }}
          categoryName={activeChatCategory.name}
          categoryDescription={activeChatCategory.description}
          onSendMessage={handleSendChatMessage}
        />
      )}
    </div>
  );
}
