import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatCardModule } from '@angular/material/card';
import { MatDividerModule } from '@angular/material/divider';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    RouterOutlet,
    FormsModule,
    CommonModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatCardModule,
    MatDividerModule,
    MatProgressSpinnerModule
  ],
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

  exampleNegative: string = 'Prowadzący nie potrafił jasno przekazać materiału, co utrudniało zrozumienie tematu. Zajęcia były chaotyczne i brakowało im struktury. Często odbiegał od tematu, co wprowadzało zamieszanie. Nie odpowiadał wyczerpująco na pytania studentów. Ogólnie prowadzenie zajęć pozostawiało wiele do życzenia.';
  examplePositive: string = 'Prowadzący był doskonale przygotowany, przekazywał materiał w sposób jasny i zorganizowany. Zachęcał do aktywnego udziału i wyczerpująco odpowiadał na pytania. Zajęcia miały logiczną strukturę, co znacząco ułatwiało przyswajanie wiedzy.';

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
