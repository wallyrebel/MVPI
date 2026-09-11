import snapshot from '../data/volleyball/current.json';
import schedule from '../data/volleyball/matches.json';

export type Ranking = typeof snapshot.rankings[number];

// matches.json stores each match once with `tournament`/`neutral` only when
// true, so the JSON import widens them away. Describe the shape explicitly.
export type RawMatch = {
  date: string | null;
  home: string;
  away: string;
  home_sets: number;
  away_sets: number;
  tournament?: boolean;
  neutral?: boolean;
};

export type TeamMatch = {
  date: string | null;
  opponentId: string;
  opponent: string;
  opponentRank: number | null;
  opponentMvpi: number | null;
  setsFor: number;
  setsAgainst: number;
  won: boolean;
  site: 'Home' | 'Away' | 'Neutral';
  tournament: boolean;
};

const matches = schedule.matches as RawMatch[];
const labels = schedule.labels as Record<string, string>;

const byId = new Map(snapshot.rankings.map((row) => [row.team_id, row]));

const byTeam = new Map<string, RawMatch[]>();
for (const match of matches) {
  for (const id of [match.home, match.away]) {
    const list = byTeam.get(id);
    if (list) list.push(match);
    else byTeam.set(id, [match]);
  }
}

export const generatedAt = snapshot.metadata.generated_at;
export const scheduleGeneratedAt = schedule.metadata.generated_at;
export const rankings = snapshot.rankings;

export function getTeam(teamId: string): Ranking | undefined {
  return byId.get(teamId);
}

/** Opponent display name, covering out-of-state teams that are never ranked. */
export function teamLabel(teamId: string): string {
  return byId.get(teamId)?.team ?? labels[teamId] ?? teamId;
}

/** Every ranked team in a classification, in statewide order. */
export function classPeers(classification: string): Ranking[] {
  return snapshot.rankings.filter((row) => row.classification === classification);
}

/** 1-based position within the team's own classification. */
export function classRank(row: Ranking): number {
  return classPeers(row.classification).findIndex((peer) => peer.team_id === row.team_id) + 1;
}

/** A team's season, oldest match first. */
export function teamSchedule(teamId: string): TeamMatch[] {
  const own = byTeam.get(teamId) ?? [];
  return own
    .map((match): TeamMatch => {
      const isHome = match.home === teamId;
      const opponentId = isHome ? match.away : match.home;
      const setsFor = isHome ? match.home_sets : match.away_sets;
      const setsAgainst = isHome ? match.away_sets : match.home_sets;
      const opponent = byId.get(opponentId);
      return {
        date: match.date,
        opponentId,
        opponent: teamLabel(opponentId),
        opponentRank: opponent?.rank ?? null,
        opponentMvpi: opponent?.mvpi ?? null,
        setsFor,
        setsAgainst,
        won: setsFor > setsAgainst,
        site: match.neutral ? 'Neutral' : isHome ? 'Home' : 'Away',
        tournament: Boolean(match.tournament),
      };
    })
    .sort((a, b) => (a.date ?? '').localeCompare(b.date ?? ''));
}

export function formatDate(value: string | null): string {
  if (!value) return '—';
  return new Date(`${value}T12:00:00`).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  });
}

export function longDate(value: string): string {
  return new Date(`${value}T12:00:00`).toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });
}
