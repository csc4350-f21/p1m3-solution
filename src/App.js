import './App.css';
import React, { useState, useRef } from 'react';

function App() {
  const args = (document.getElementById('data') == null) ? ({
    artist_ids: [],
    username: 'John',
    has_artists_saved: false,
  }) : JSON.parse(document.getElementById('data').text);
  const [artists, updateArtists] = useState(args.artist_ids);
  const form = useRef(null);

  function onClickAdd() {
    const val = form.current.value;
    const updatedArtists = [...artists, val];
    updateArtists(updatedArtists);
    form.current.value = '';
  }

  function onClickDelete(i) {
    const updatedArtists = [...artists.slice(0, i), ...artists.slice(i + 1)];
    updateArtists(updatedArtists);
  }

  function onClickSave() {
    const requestData = { artist_ids: artists };
    fetch('/save', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestData),
    })
      .then((response) => response.json())
      .then((data) => {
        updateArtists(data.artist_ids);
      });
  }

  const deleteButtonStyle = {
    backgroundColor: 'red',
    border: 'none',
    color: 'white',
    padding: '15px 32px',
    textAlign: 'center',
    textDecoration: 'none',
    display: 'inline-block',
    fontSize: '16px',
  };

  const gridStyle = {
    align: 'center',
    display: 'grid',
    gridTemplateColumns: '2fr 1fr',
    gridGap: '10px 5px',
    marginLeft: '30%',
    marginRight: '30%',
  };

  const artistsList = artists.map((artistID, i) => (
    <div style={gridStyle}>
      <p>{artistID}</p>
      <button type="button" style={deleteButtonStyle} onClick={() => onClickDelete(i)}>Delete</button>
    </div>
  ));

  return (
    <div>
      <h1>
        {args.username}
        &apos;s Song Explorer
      </h1>
      {args.has_artists_saved ? (
        <>
          <h2>{args.song_name}</h2>
          <h3>{args.song_artist}</h3>
          <div>
            <img alt="" src={args.song_image_url} width={300} height={300} />
          </div>
          <div>
            <audio controls>
              <source src={args.preview_url} />
            </audio>
          </div>
          <a href={args.genius_url}> Click here to see lyrics! </a>

        </>
      ) : (
        <h2>Looks like you don&apos;t have anything saved! Use the form below!</h2>
      )}
      <h1>Your saved artists:</h1>
      {artistsList}
      <h1>Save a favorite artist ID for later:</h1>
      <input type="text" ref={form} data-testid="text_input" />
      <button type="button" onClick={onClickAdd}>Add Artist</button>
      <button type="button" onClick={onClickSave}>Save</button>
    </div>
  );
}

export default App;
