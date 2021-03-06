
var express = require('express');

var app = express();

var PORT = 3000;

const Agenda = require('agenda');

app.listen(PORT, function() {
    console.log('Server is running on PORT:',PORT);
});

const fs = require('fs');
const readline = require('readline');
const {google} = require('googleapis');

var datum = new Date();
var CurrentUnixTime = (datum.getTime() / 1000).toFixed(0);

var storedAuth;

setInterval(() => {
  listEvents(storedAuth);
},10000);

// If modifying these scopes, delete token.json.
const SCOPES = ['https://www.googleapis.com/auth/calendar.readonly'];
// The file token.json stores the user's access and refresh tokens, and is
// created automatically when the authorization flow completes for the first
// time.
const TOKEN_PATH = 'token.json';

// Load client secrets from a local file.
fs.readFile('credentials.json', (err, content) => {
  if (err) return console.log('Error loading client secret file:', err);
  // Authorize a client with credentials, then call the Google Calendar API.
  authorize(JSON.parse(content), function(auth) {
    storedAuth = auth;
    listEvents(storedAuth);
  });
});

/**
 * Create an OAuth2 client with the given credentials, and then execute the
 * given callback function.
 * @param {Object} credentials The authorization client credentials.
 * @param {function} callback The callback to call with the authorized client.
 */
function authorize(credentials, callback) {
  const {client_secret, client_id, redirect_uris} = credentials.installed;
  const oAuth2Client = new google.auth.OAuth2(
      client_id, client_secret, redirect_uris[0]);

  // Check if we have previously stored a token.
  fs.readFile(TOKEN_PATH, (err, token) => {
    if (err) return getAccessToken(oAuth2Client, callback);
    oAuth2Client.setCredentials(JSON.parse(token));
    callback(oAuth2Client);
  });
}

/**
 * Get and store new token after prompting for user authorization, and then
 * execute the given callback with the authorized OAuth2 client.
 * @param {google.auth.OAuth2} oAuth2Client The OAuth2 client to get token for.
 * @param {getEventsCallback} callback The callback for the authorized client.
 */
function getAccessToken(oAuth2Client, callback) {
  const authUrl = oAuth2Client.generateAuthUrl({
    access_type: 'offline',
    scope: SCOPES,
  });
  console.log('Authorize this app by visiting this url:', authUrl);
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });
  rl.question('Enter the code from that page here: ', (code) => {
    rl.close();
    oAuth2Client.getToken(code, (err, token) => {
      if (err) return console.error('Error retrieving access token', err);
      oAuth2Client.setCredentials(token);
      // Store the token to disk for later program executions
      fs.writeFile(TOKEN_PATH, JSON.stringify(token), (err) => {
        if (err) return console.error(err);
        console.log('Token stored to', TOKEN_PATH);
      });
      callback(oAuth2Client);
    });
  });
}

function writeToFile(SummaryEvent) {
  fs.readFile('Content.txt', (err, data) => {
    if (err) throw err;
    console.log(data.toString());
    if (data.toString() == SummaryEvent){
      console.log('Events match');
    } else {
      fs.writeFile("Content.txt", SummaryEvent, (err) => {
        if (err) return console.error(err);
        console.log('Token stored to', "Content.txt");
      });
    }
  });
}

/**
 * Lists the next 10 events on the user's primary calendar.
 * @param {google.auth.OAuth2} auth An authorized OAuth2 client.
 */
function listEvents(auth) {
  const calendar = google.calendar({version: 'v3', auth});
  calendar.events.list({
    calendarId: 'primary',
    timeMin: (new Date()).toISOString(),
    maxResults: 10,
    singleEvents: true,
    orderBy: 'startTime',
  }, (err, res) => {
    if (err) return console.log('The API returned an error: ' + err);
    const events = res.data.items;
    if (events.length) {
      //Pak ieder event 
      events.forEach(event=>{
      
        FirstEventTime = new Date(event.start.dateTime);
        SecondEventTime = new Date(event.end.dateTime)
        SummaryEvent = event.summary;
        FirstUnixTime = FirstEventTime.getTime() /1000;
        SecondUnixTime = SecondEventTime.getTime() /1000;
        
        if (CurrentUnixTime >= FirstUnixTime && CurrentUnixTime <= SecondUnixTime){
          console.log("Times Match", SummaryEvent);
          writeToFile(SummaryEvent);
        }
        
      })
    } else {
      console.log('No upcoming events found.');
    }
  });
}