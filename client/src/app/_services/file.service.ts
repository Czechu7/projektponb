import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { User } from '../_models/user';
import { map } from 'rxjs';
import { Products } from '../_models/products';
import { Cart } from '../_models/cart';

@Injectable({
  providedIn: 'root'
})
export class FileService {
  private http = inject(HttpClient);
  baseUrl = "http://localhost:4999/api/files";
  currentUser = signal<User | null>(null)

  uploadFile(file: File) {
    const formData = new FormData();
    formData.append('file', file, file.name);
    
    return this.http.post(this.baseUrl, formData, {
      reportProgress: true,  
      observe: 'events'  
    });
  }
 

}
