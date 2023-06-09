# -*- coding: utf-8 -*-
"""machine_learning_model.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Te6rgZ_-64jzQ_ptWXnST3LUxM-7Vanf
"""

import torch
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from torch.utils.data import Dataset, DataLoader
from torch.nn.utils.rnn import pad_sequence
from torch import nn
import torchtext
from torch.nn.modules import dropout

# Load and preprocess the data
df = pd.read_csv('train.csv')

df.head()

df.describe

tokenizer = torchtext.data.utils.get_tokenizer('basic_english')
lyrics = []
for lyric in df['Lyric']:
    tokenized_lyric = tokenizer(lyric)
    lyrics.append(tokenized_lyric)
artists = df['Artist'].tolist()
genres = df['Genre'].tolist()

# Encode categorical features
artist_encoder = LabelEncoder()
genre_encoder = LabelEncoder()
artist_encoded = artist_encoder.fit_transform(artists)
genre_encoded = genre_encoder.fit_transform(genres)

# Create a vocabulary and encode tokens
vocab = set(token for lyric in lyrics for token in lyric)
vocab_to_idx = {token: idx+1 for idx, token in enumerate(vocab)}

lyrics_encoded = [[vocab_to_idx[token] for token in lyric] for lyric in lyrics]

# Pad sequences to a fixed length
max_seq_length = 250
lyrics_padded = [torch.LongTensor(seq[:max_seq_length]) if len(seq) > max_seq_length else torch.LongTensor(seq) for seq in lyrics_encoded]
X = torch.nn.utils.rnn.pad_sequence(lyrics_padded, batch_first=True).transpose(1,0)

# Convert data to PyTorch tensors
y_artist = torch.LongTensor(artist_encoded)
y_genre = torch.LongTensor(genre_encoded)

# Define a PyTorch dataset
class SongLyricsDataset(Dataset):
    def __init__(self, lyrics, artists, genres):
        self.lyrics = lyrics
        self.artists = artists
        self.genres = genres

    def __len__(self):
        return len(self.lyrics)

    def __getitem__(self, idx):
        return self.lyrics[idx], self.artists[idx], self.genres[idx]

# Split data into training and test sets
num_samples = len(X)
split_ratio = 0.8
split_idx = int(num_samples*split_ratio)

train_dataset = SongLyricsDataset(X[:split_idx], y_artist[:split_idx], y_genre[:split_idx])
test_dataset = SongLyricsDataset(X[split_idx:], y_artist[split_idx:], y_genre[split_idx:])


class LyricsClassifier(nn.Module):
    def __init__(self, vocab_size, num_artists, num_genres, hidden_size, dropout):
        """
        Define a PyTorch model for classifying song lyrics.

        Args:
        - vocab_size (int): The size of the vocabulary used to represent the lyrics.
        - num_artists (int): The number of possible artist labels.
        - num_genres (int): The number of possible genre labels.
        - hidden_size (int): The size of the hidden layer of the LSTM.
        - dropout (float): The dropout probability to apply to the LSTM outputs.
        """
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, hidden_size)
        self.lstm = nn.LSTM(hidden_size, hidden_size, batch_first=True)
        self.dropout = nn.Dropout(dropout)
        self.fc_artist = nn.Linear(hidden_size, num_artists)
        self.fc_genre = nn.Linear(hidden_size, num_genres)

    def forward(self, input_sequence):
        """
        Forward pass of the lyrics classifier model.

        Args:
        - input_sequence (torch.Tensor): The input sequence of lyrics as a tensor of shape (batch_size, sequence_length)

        Returns:
        - artist_logits (torch.Tensor): The logits for the artist classification as a tensor of shape (batch_size, num_artists)
        - genre_logits (torch.Tensor): The logits for the genre classification as a tensor of shape (batch_size, num_genres)
        """
        # Embed the input sequence
        embedded_sequence = self.embedding(input_sequence)

        # Pass the embedded sequence through the LSTM
        lstm_outputs, _ = self.lstm(embedded_sequence)

        # Apply dropout to the LSTM outputs
        lstm_outputs = self.dropout(lstm_outputs)

        # Flatten the final LSTM output and pass it through the artist and genre classifiers
        flattened_outputs = lstm_outputs[:, -1, :]
        artist_logits = self.fc_artist(flattened_outputs)
        genre_logits = self.fc_genre(flattened_outputs)

        return artist_logits, genre_logits

# Define hyperparameters
input_size = len(vocab_to_idx) + 1 # add 1 for padding token
num_artists = len(artist_encoder.classes_)
num_genres = len(genre_encoder.classes_)
hidden_size = 8
dropout_rate = 0.2
learning_rate = 0.1

device = 'cuda' if torch.cuda.is_available() else 'cpu'

# Initialize the model and optimizer

model_0 = LyricsClassifier(input_size, num_artists, num_genres, hidden_size,dropout=dropout_rate)
optimizer = torch.optim.Adam(model_0.parameters(), lr=learning_rate)


# Define the loss function
loss_fn = nn.CrossEntropyLoss()

batch_size = 32

train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

# Train the model
num_epochs = 8

for epoch in range(num_epochs):
    model_0.train()
    train_loss = 0
    train_acc_artist = 0
    train_acc_genre = 0
    num_train_samples = 0
    
    for i, (x, y_artist_true, y_genre_true) in enumerate(train_loader):
        x = x.to(device)
        y_artist_true = y_artist_true.to(device)
        y_genre_true = y_genre_true.to(device)

        optimizer.zero_grad()

        y_artist_pred, y_genre_pred = model_0(x)
        loss_artist = loss_fn(y_artist_pred, y_artist_true)
        loss_genre = loss_fn(y_genre_pred, y_genre_true)
        loss = loss_artist + loss_genre

        loss.backward()
        optimizer.step()

        with torch.no_grad():
            train_loss += loss.item() * x.shape[0]
            train_acc_artist += (y_artist_pred.argmax(dim=-1) == y_artist_true).sum().item()
            train_acc_genre += (y_genre_pred.argmax(dim=-1) == y_genre_true).sum().item()
            num_train_samples += len(x)

    train_loss /= num_train_samples
    train_acc_artist /= num_train_samples
    train_acc_genre /= num_train_samples

    # Evaluate the model
    model_0.eval()
    test_loss = 0
    test_acc_artist = 0
    test_acc_genre = 0
    num_test_samples = 0

    for i, (x, y_artist_true, y_genre_true) in enumerate(test_loader):
        x = x.to(device)
        y_artist_true = y_artist_true.to(device)
        y_genre_true = y_genre_true.to(device)

        y_artist_pred, y_genre_pred = model_0(x)
        loss_artist = loss_fn(y_artist_pred, y_artist_true)
        loss_genre = loss_fn(y_genre_pred, y_genre_true)
        loss = loss_artist + loss_genre

        with torch.inference_mode():
            test_loss += loss.item() * x.shape[0]
            test_acc_artist += (y_artist_pred.argmax(dim=-1) == y_artist_true).sum().item()
            test_acc_genre += (y_genre_pred.argmax(dim=-1) == y_genre_true).sum().item()
            num_test_samples += len(x)

    test_loss /= num_test_samples
    test_acc_artist /= num_test_samples
    test_acc_genre /= num_test_samples

    print(f'Epoch {epoch+1}/{num_epochs}, Train Loss: {train_loss:.4f}, Train Artist Acc: {train_acc_artist:.4f}, Train Genre Acc: {train_acc_genre:.4f}, Test Loss: {test_loss:.4f}, Test Artist Acc: {test_acc_artist:.4f}, Test Genre Acc: {test_acc_genre:.4f}')

#Define a function to predict artist and genre from lyrics

def predict_lyrics(model, vocab_to_idx, artist_encoder, genre_encoder, lyrics):
    model.eval()
    tokens = tokenizer(lyrics)
    encoded = [[vocab_to_idx.get(token, 0) for token in tokens]]
    padded = [torch.LongTensor(seq[:max_seq_length] + [0]*(max_seq_length-len(seq))) for seq in encoded]
    x = pad_sequence(padded, batch_first=True)
    artist_logits, genre_logits = model(x.to(device))
    artist_pred = artist_encoder.inverse_transform(artist_logits.argmax(dim=-1).cpu().numpy())[0]
    genre_pred = genre_encoder.inverse_transform(genre_logits.argmax(dim=-1).cpu().numpy())[0]
    return artist_pred, genre_pred

# enter some lyrics and see how the model performs
lyrics = input("Enter some lyrics: ")
artist_pred, genre_pred = predict_lyrics(model_0, vocab_to_idx, artist_encoder, genre_encoder, lyrics)
print(f"Predicted Artist: {artist_pred}, Predicted Genre: {genre_pred}")













