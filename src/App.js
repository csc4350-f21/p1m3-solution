import './App.css';
import React, { useState, useRef } from 'react';


function App() {
  const args = JSON.parse(document.getElementById("data").text);
  const [artists, updateArtists] = useState(args.artist_ids);
  const form = useRef(null);

  function onClickAdd() {
    let val = form.current.value;
    let updatedArtists = [...artists, val];
    updateArtists(updatedArtists);
    form.current.value = "";
    console.log(updatedArtists);
  }

  function onClickDelete(i) {
    let updatedArtists = [...artists.slice(0, i), ...artists.slice(i + 1)];
    updateArtists(updatedArtists);
  }

  function onClickSave() {
    let data = { "artist_ids": artists };
    console.log(JSON.stringify(data))
    fetch('/save', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })
      .then(response => response.json())
      .then(data => {
        console.log('Success:', data)
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

  const artists_list = artists.map((artist_id, i) => (
    <div style={gridStyle}>
      <p>{artist_id}</p>
      <button style={deleteButtonStyle} onClick={() => onClickDelete(i)}>Delete</button>
    </div>
  ));

  return (
    <div>
      <h1>{args.username}'s Song Explorer</h1>
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
          <h1>Your saved artists:</h1>
          {artists_list}
        </>
      ) : (
        <h2>Looks like you don't have anything saved! Use the form below!</h2>
      )}
      <h1>Save a favorite artist ID for later:</h1>
      <input type="text" ref={form}></input>
      <button onClick={onClickAdd}>Add Artist</button>
      <button onClick={onClickSave}>Save</button>
    </div>
  );
}

export default App;
