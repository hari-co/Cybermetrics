import React from 'react';
import styles from './PlayerCard.module.css';

interface StatsCategoryProps {
  title: string;
  children: React.ReactNode;
}

export const StatsCategory: React.FC<StatsCategoryProps> = ({ title, children }) => {
  return (
    <div className={styles.statsCategory}>
      <h4 className={styles.categoryTitle}>{title}</h4>
      {children}
    </div>
  );
};

