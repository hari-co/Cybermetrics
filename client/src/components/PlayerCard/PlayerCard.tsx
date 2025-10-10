import { useEffect, useState } from "react";
import { PlayerDetail, PlayerHittingStats } from "@/api/players";
import { playerActions } from "@/actions/players";
import Button from "@/components/Button";
import Spinner from "@/components/Spinner";
import { StatItem } from "./StatItem";
import { StatsCategory } from "./StatsCategory";
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
      
      if (result.success && result.data) {
        setPlayer(result.data);
        
        // Fetch stats using Fangraphs ID if available
        const fangraphsId = result.data.key_fangraphs || playerId;
        setStatsLoading(true);
        const statsResult = await playerActions.getPlayerStats(fangraphsId);
        setStatsLoading(false);
        
        if (statsResult.success && statsResult.data && statsResult.data.length > 0) {
          setStats(statsResult.data);
          // Set the most recent season as default
          const mostRecent = statsResult.data.reduce((prev, current) => 
            (current.season > prev.season) ? current : prev
          );
          setSelectedSeason(mostRecent.season);
        }
      } else {
        setError(result.error || 'Failed to load player details');
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
                        <StatsCategory title="Basic">
                          <StatItem label="AVG" value={formatStat(currentStats.avg)} />
                          <StatItem label="OBP" value={formatStat(currentStats.obp)} />
                          <StatItem label="SLG" value={formatStat(currentStats.slg)} />
                          <StatItem label="OPS" value={formatStat(currentStats.ops)} />
                          <StatItem label="HR" value={formatStat(currentStats.home_runs, 0)} />
                          <StatItem label="RBI" value={formatStat(currentStats.rbi, 0)} />
                        </StatsCategory>

                        <StatsCategory title="Advanced">
                          <StatItem label="K%" value={formatPercent(currentStats.k_percent)} />
                          <StatItem label="BB%" value={formatPercent(currentStats.bb_percent)} />
                          <StatItem label="ISO" value={formatStat(currentStats.iso)} />
                          <StatItem label="wOBA" value={formatStat(currentStats.woba)} />
                          <StatItem label="wRC+" value={formatStat(currentStats.wrc_plus, 0)} />
                          <StatItem label="WAR" value={formatStat(currentStats.war, 1)} />
                        </StatsCategory>

                        {(currentStats.barrel_percent || currentStats.hard_hit_percent || currentStats.avg_exit_velocity) && (
                          <StatsCategory title="Statcast">
                            {currentStats.barrel_percent && (
                              <StatItem label="Barrel%" value={formatPercent(currentStats.barrel_percent)} />
                            )}
                            {currentStats.hard_hit_percent && (
                              <StatItem label="HardHit%" value={formatPercent(currentStats.hard_hit_percent)} />
                            )}
                            {currentStats.avg_exit_velocity && (
                              <StatItem label="EV" value={formatStat(currentStats.avg_exit_velocity, 1)} />
                            )}
                            {currentStats.xwoba && (
                              <StatItem label="xwOBA" value={formatStat(currentStats.xwoba)} />
                            )}
                          </StatsCategory>
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

