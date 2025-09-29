import { useState } from 'react';

const PlayerSearch: React.FC = () => {
    const [query, setQuery] = useState('');

    return (
        <div>
            <h1>Player Search</h1>
            <input type="text" className='h-10 w-80 rounded-lg border-2 border-black p-2' placeholder='Search for a player...' />
        </div>
    )
}

export default PlayerSearch;