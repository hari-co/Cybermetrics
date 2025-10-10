import { useEffect, useState } from "react";
import { PlayerDetail, PlayerHittingStats } from "@/api/players";
import { playerActions } from "@/actions/players";
import Button from "@/components/Button";
import Spinner from "@/components/Spinner";
import styles from "./PlayerCard.module.css";

interface PlayerCardProps {
  playerId: number;
  onClose: () => void;
}

export default function PlayerCard({ playerId, onClose }: PlayerCardProps) {
  const [player, setPlayer] = useState<PlayerDetail | null>(null);
  const [stats, setStats] = useState<PlayerHittingStats[]>([]);
  const [selectedSeason, setSelectedSeason] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [statsLoading, setStatsLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchPlayerDetail = async () => {
      setIsLoading(true);
      const result = await playerActions.getPlayerDetail(playerId);
      
      if (result.success) {
        setPlayer(result.data);
        
        // Fetch stats using Fangraphs ID if available
        const fangraphsId = result.data.key_fangraphs || playerId;
        setStatsLoading(true);
        const statsResult = await playerActions.getPlayerStats(fangraphsId);
        setStatsLoading(false);
        
        if (statsResult.success && statsResult.data.length > 0) {
          setStats(statsResult.data);
          // Set the most recent season as default
          const mostRecent = statsResult.data.reduce((prev, current) => 
            (current.season > prev.season) ? current : prev
          );
          setSelectedSeason(mostRecent.season);
        }
      } else {
        setError(result.error);
      }
      
      setIsLoading(false);
    };

    fetchPlayerDetail();
  }, [playerId]);

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className={styles.overlay} onClick={handleOverlayClick}>
      <div className={styles.modal}>
        <button className={styles.closeButton} onClick={onClose}>
          ×
        </button>

        {isLoading && (
          <div className={styles.loading}>
            <Spinner />
          </div>
        )}

        {error && (
          <div className={styles.error}>
            <p>Error loading player details</p>
            <p className={styles.errorMessage}>{error}</p>
            <Button onClick={onClose} variant="secondary">Close</Button>
          </div>
        )}

        {player && !isLoading && (
          <div className={styles.content}>
            <div className={styles.header}>
              <img
                src={player.image_url}
                alt={player.name}
                className={styles.playerImage}
                onError={(e) => {
                  e.currentTarget.src = 'https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/0/headshot/67/current';
                }}
              />
              <div className={styles.headerInfo}>
                <h2 className={styles.playerName}>{player.name}</h2>
                {player.years_active && <p className={styles.yearsActive}>{player.years_active}</p>}
              </div>
            </div>

            <div className={styles.details}>
              <div className={styles.detailRow}>
                <span className={styles.label}>MLB ID:</span>
                <span className={styles.value}>{player.id}</span>
              </div>
              
              {player.first_name && (
                <div className={styles.detailRow}>
                  <span className={styles.label}>First Name:</span>
                  <span className={styles.value}>{player.first_name}</span>
                </div>
              )}

              {player.last_name && (
                <div className={styles.detailRow}>
                  <span className={styles.label}>Last Name:</span>
                  <span className={styles.value}>{player.last_name}</span>
                </div>
              )}

              {player.mlb_played_first && (
                <div className={styles.detailRow}>
                  <span className={styles.label}>First Year in MLB:</span>
                  <span className={styles.value}>{player.mlb_played_first}</span>
                </div>
              )}

              {player.mlb_played_last && (
                <div className={styles.detailRow}>
                  <span className={styles.label}>Last Year in MLB:</span>
                  <span className={styles.value}>{player.mlb_played_last}</span>
                </div>
              )}

              {player.key_retro && (
                <div className={styles.detailRow}>
                  <span className={styles.label}>Retrosheet ID:</span>
                  <span className={styles.value}>{player.key_retro}</span>
                </div>
              )}

              {player.key_bbref && (
                <div className={styles.detailRow}>
                  <span className={styles.label}>Baseball Reference ID:</span>
                  <span className={styles.value}>{player.key_bbref}</span>
                </div>
              )}

              {player.key_fangraphs && (
                <div className={styles.detailRow}>
                  <span className={styles.label}>Fangraphs ID:</span>
                  <span className={styles.value}>{player.key_fangraphs}</span>
                </div>
              )}
            </div>

            {stats.length > 0 && (
              <div className={styles.statsSection}>
                <h3 className={styles.statsHeader}>Hitting Statistics</h3>
                
                {/* Season Selector */}
                {stats.length > 1 && (
                  <div className={styles.seasonSelector}>
                    {stats
                      .sort((a, b) => b.season - a.season)
                      .map((stat) => (
                        <button
                          key={stat.season}
                          className={`${styles.seasonButton} ${selectedSeason === stat.season ? styles.seasonButtonActive : ''}`}
                          onClick={() => setSelectedSeason(stat.season)}
                        >
                          {stat.season}
                        </button>
                      ))}
                  </div>
                )}

                {statsLoading ? (
                  <div className={styles.statsLoading}>
                    <Spinner />
                  </div>
                ) : (
                  selectedSeason && (() => {
                    const currentStats = stats.find(s => s.season === selectedSeason);
                    if (!currentStats) return null;

                    const formatStat = (value: number | undefined | null, decimals = 3): string => {
                      if (value === null || value === undefined) return '-';
                      return decimals === 0 ? value.toString() : value.toFixed(decimals);
                    };

                    const formatPercent = (value: number | undefined | null): string => {
                      if (value === null || value === undefined) return '-';
                      return `${(value * 100).toFixed(1)}%`;
                    };

                    return (
                      <div className={styles.statsGrid}>
                        {/* Basic Stats */}
                        <div className={styles.statsCategory}>
                          <h4 className={styles.categoryTitle}>Basic</h4>
                          <div className={styles.statItem}>
                            <span className={styles.statLabel}>AVG</span>
                            <span className={styles.statValue}>{formatStat(currentStats.avg)}</span>
                          </div>
                          <div className={styles.statItem}>
                            <span className={styles.statLabel}>OBP</span>
                            <span className={styles.statValue}>{formatStat(currentStats.obp)}</span>
                          </div>
                          <div className={styles.statItem}>
                            <span className={styles.statLabel}>SLG</span>
                            <span className={styles.statValue}>{formatStat(currentStats.slg)}</span>
                          </div>
                          <div className={styles.statItem}>
                            <span className={styles.statLabel}>OPS</span>
                            <span className={styles.statValue}>{formatStat(currentStats.ops)}</span>
                          </div>
                          <div className={styles.statItem}>
                            <span className={styles.statLabel}>HR</span>
                            <span className={styles.statValue}>{formatStat(currentStats.home_runs, 0)}</span>
                          </div>
                          <div className={styles.statItem}>
                            <span className={styles.statLabel}>RBI</span>
                            <span className={styles.statValue}>{formatStat(currentStats.rbi, 0)}</span>
                          </div>
                        </div>

                        {/* Advanced Stats */}
                        <div className={styles.statsCategory}>
                          <h4 className={styles.categoryTitle}>Advanced</h4>
                          <div className={styles.statItem}>
                            <span className={styles.statLabel}>K%</span>
                            <span className={styles.statValue}>{formatPercent(currentStats.k_percent)}</span>
                          </div>
                          <div className={styles.statItem}>
                            <span className={styles.statLabel}>BB%</span>
                            <span className={styles.statValue}>{formatPercent(currentStats.bb_percent)}</span>
                          </div>
                          <div className={styles.statItem}>
                            <span className={styles.statLabel}>ISO</span>
                            <span className={styles.statValue}>{formatStat(currentStats.iso)}</span>
                          </div>
                          <div className={styles.statItem}>
                            <span className={styles.statLabel}>wOBA</span>
                            <span className={styles.statValue}>{formatStat(currentStats.woba)}</span>
                          </div>
                          <div className={styles.statItem}>
                            <span className={styles.statLabel}>wRC+</span>
                            <span className={styles.statValue}>{formatStat(currentStats.wrc_plus, 0)}</span>
                          </div>
                          <div className={styles.statItem}>
                            <span className={styles.statLabel}>WAR</span>
                            <span className={styles.statValue}>{formatStat(currentStats.war, 1)}</span>
                          </div>
                        </div>

                        {/* Statcast Metrics */}
                        {(currentStats.barrel_percent || currentStats.hard_hit_percent || currentStats.avg_exit_velocity) && (
                          <div className={styles.statsCategory}>
                            <h4 className={styles.categoryTitle}>Statcast</h4>
                            {currentStats.barrel_percent && (
                              <div className={styles.statItem}>
                                <span className={styles.statLabel}>Barrel%</span>
                                <span className={styles.statValue}>{formatPercent(currentStats.barrel_percent)}</span>
                              </div>
                            )}
                            {currentStats.hard_hit_percent && (
                              <div className={styles.statItem}>
                                <span className={styles.statLabel}>HardHit%</span>
                                <span className={styles.statValue}>{formatPercent(currentStats.hard_hit_percent)}</span>
                              </div>
                            )}
                            {currentStats.avg_exit_velocity && (
                              <div className={styles.statItem}>
                                <span className={styles.statLabel}>EV</span>
                                <span className={styles.statValue}>{formatStat(currentStats.avg_exit_velocity, 1)}</span>
                              </div>
                            )}
                            {currentStats.xwoba && (
                              <div className={styles.statItem}>
                                <span className={styles.statLabel}>xwOBA</span>
                                <span className={styles.statValue}>{formatStat(currentStats.xwoba)}</span>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })()
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

