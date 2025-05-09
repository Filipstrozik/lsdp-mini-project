import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { HttpClientModule } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, HttpClientModule, FormsModule, CommonModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent {
  title = 'Predyktor oceny opinii prowadzącego';
  inputText = '';
  rating: number | null = null;
  confidence: number | null = null;
  loading = false;
  error: string | null = null;

  constructor(private http: HttpClient) {}

  send() {
    if (!this.inputText) return;
    this.loading = true;
    this.error = null;
    this.rating = null;
    this.confidence = null;
    const query = `query ($text: String!) { predict(text: $text) { rating confidence } }`;
    const body = { query, variables: { text: this.inputText } };
    this.http.post<any>('http://localhost:5000/graphql', body).subscribe(
      res => {
        const data = res.data.predict;
        this.rating = data.rating;
        this.confidence = data.confidence;
        this.loading = false;
      },
      err => {
        this.error = 'Błąd serwera';
        this.loading = false;
      }
    );
  }
}
