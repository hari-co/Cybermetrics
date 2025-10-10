import { apiClient } from "@/api/client";

export interface PlayerSearchResult {
  id: number;
  name: string;
  score: number;
  image_url: string;
  years_active: string;
}

export interface SavedPlayer {
  id: number;
  name: string;
  image_url?: string;
  years_active?: string;
  [key: string]: any; // Allow additional fields
}

export interface PlayerDetail {
  id: number;
  name: string;
  image_url: string;
  years_active?: string;
  first_name?: string;
  last_name?: string;
  mlb_played_first?: string;
  mlb_played_last?: string;
  key_retro?: string;
  key_bbref?: string;
  key_fangraphs?: number;
}

export interface AddPlayerResponse {
  message: string;
  player_id: string;
}

export interface DeletePlayerResponse {
  message: string;
}

export interface PlayerHittingStats {
  fangraphs_id: number;
  mlb_player_id?: number;
  name: string;
  team?: string;
  season: number;
  age?: number;
  
  // Basic counting stats
  games?: number;
  at_bats?: number;
  plate_appearances?: number;
  hits?: number;
  doubles?: number;
  triples?: number;
  home_runs?: number;
  runs?: number;
  rbi?: number;
  stolen_bases?: number;
  caught_stealing?: number;
  
  // Required stats
  k_percent?: number;
  bb_percent?: number;
  obp?: number;
  iso?: number;
  bsr?: number;
  
  // Advanced metrics
  woba?: number;
  wrc_plus?: number;
  avg?: number;
  slg?: number;
  ops?: number;
  babip?: number;
  war?: number;
  
  // Statcast metrics
  barrel_percent?: number;
  hard_hit_percent?: number;
  avg_exit_velocity?: number;
  max_exit_velocity?: number;
  avg_launch_angle?: number;
  xba?: number;
  xslg?: number;
  xwoba?: number;
  
  // Plate discipline
  o_swing_percent?: number;
  z_swing_percent?: number;
  swing_percent?: number;
  o_contact_percent?: number;
  z_contact_percent?: number;
  contact_percent?: number;
  zone_percent?: number;
  swstr_percent?: number;
  
  // Batted ball data
  gb_percent?: number;
  fb_percent?: number;
  ld_percent?: number;
  pull_percent?: number;
  cent_percent?: number;
  oppo_percent?: number;
  soft_percent?: number;
  med_percent?: number;
  hard_percent?: number;
  
  // Additional value metrics
  wraa?: number;
  wrc?: number;
  off?: number;
  def_value?: number;
  wsb?: number;
  ubr?: number;
  spd?: number;
}

export const playersApi = {
  search: async (query: string): Promise<PlayerSearchResult[]> => {
    return apiClient.get<PlayerSearchResult[]>(`/api/players/search?q=${encodeURIComponent(query)}`);
  },

  getDetail: async (playerId: number): Promise<PlayerDetail> => {
    return apiClient.get<PlayerDetail>(`/api/players/${playerId}/detail`);
  },

  getSaved: async (): Promise<SavedPlayer[]> => {
    return apiClient.get<SavedPlayer[]>("/api/players/saved");
  },

  addSaved: async (player: { id: number; name: string; image_url?: string; years_active?: string }): Promise<AddPlayerResponse> => {
    return apiClient.post<AddPlayerResponse>("/api/players/saved", player);
  },

  deleteSaved: async (playerId: number): Promise<DeletePlayerResponse> => {
    return apiClient.delete<DeletePlayerResponse>(`/api/players/saved/${playerId}`);
  },

  getPlayerStats: async (fangraphsId: number, season?: number): Promise<PlayerHittingStats[]> => {
    const seasonParam = season ? `?season=${season}` : '';
    return apiClient.get<PlayerHittingStats[]>(`/api/player-stats/${fangraphsId}${seasonParam}`);
  },
};

