import { importProvidersFrom } from '@angular/core';
import { HttpClientModule } from '@angular/common/http';
import { FormsModule } from '@angular/forms';

export const appConfig = {
  providers: [
    importProvidersFrom(HttpClientModule, FormsModule)
  ]
};
