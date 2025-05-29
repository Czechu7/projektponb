import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { User } from '../_models/user';
import { map } from 'rxjs';
import { Products } from '../_models/products';
import { Cart } from '../_models/cart';

@Injectable({
  providedIn: 'root',
})
export class FileService {
  private http = inject(HttpClient);
  baseUrlApi = 'http://localhost:4999/api/files';
  baseUrlBlockchain = 'http://localhost:5001';
  currentUser = signal<User | null>(null);

  uploadFile(file: File) {
    const formData = new FormData();
    formData.append('file', file, file.name);

    return this.http.post(this.baseUrlApi, formData, {
      reportProgress: true,
      observe: 'events',
    });
  }

  createTorrent(transactionId: string) {
    return this.http.get(
      `${this.baseUrlBlockchain}/torrent/create/${transactionId}`
    );
  }

  downloadTorrent(transactionId: string) {
    return this.http.get(
      `${this.baseUrlBlockchain}/torrent/file/${transactionId}`,
      {
        responseType: 'blob',
      }
    );
  }
}
