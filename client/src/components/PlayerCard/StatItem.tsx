import React from 'react';
import styles from './PlayerCard.module.css';

interface StatItemProps {
  label: string;
  value: string | number;
}

export const StatItem: React.FC<StatItemProps> = ({ label, value }) => {
  return (
    <div className={styles.statItem}>
      <span className={styles.statLabel}>{label}</span>
      <span className={styles.statValue}>{value}</span>
    </div>
  );
};

