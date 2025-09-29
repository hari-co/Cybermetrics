import { useState } from 'react';
import type { Player } from '../types/player'

interface PlayerSearchProps {
    onPlayerSelect(player: Player): void;
}

const PlayerSearch: React.FC<PlayerSearchProps> = ({ onPlayerSelect }) => {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState<Player[]>([]);
    const [showSuggestions, setShowSuggestions] = useState(false);

    const MIN_LEN = 3;

    const fetchResults = async (q: string) => {
        if (q.length >= MIN_LEN) {
            const response = await fetch(`/players/search?q=${q}`);
            if (!response.ok) return;
            const data = await response.json();
            setResults(data);
            setShowSuggestions(true);
        } else {
            setResults([]);
            setShowSuggestions(false);
        }
    }

    const handleSearch = async (e: React.ChangeEvent<HTMLInputElement>) => {
        setQuery(e.target.value);
        await fetchResults(e.target.value);
    };

    const handleSelect = (player: Player) => {
        onPlayerSelect(player);
        setQuery(player.name);
        setShowSuggestions(false);
    }

    return (
        <div className='flex flex-col'>
            <h1>Player Search</h1>
            <input 
            type="text" 
            className='h-10 w-80 rounded-lg border-2 border-black p-2' 
            value={query}
            placeholder='Search for a player...' 
            onChange={handleSearch}
            onFocus={() => setShowSuggestions(results.length > 0)}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 100)} />
                {showSuggestions && results.length > 0 &&(
                    <div>
                        <ul>
                            {results.map((player) => (
                                <li key={player.id}
                                    onMouseDown={() => handleSelect(player)}>
                                    {player.name}
                                </li>
                            ))}
                        </ul>
                    </div>
                )}
        </div>
    )
}

export default PlayerSearch;