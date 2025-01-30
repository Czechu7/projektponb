import { HttpClient } from '@angular/common/http';
import { HubConnection, HubConnectionBuilder } from '@microsoft/signalr';
import { inject, Injectable, signal } from '@angular/core';
import { User } from '../_models/user';
import { Observable } from 'rxjs/internal/Observable';
import { BehaviorSubject, map } from 'rxjs';
import { NodeStatus } from '../_models/nodeStatus';
import { Chain } from '../_models/chain';

@Injectable({
  providedIn: 'root'
})
export class DocumentsService {
  private http = inject(HttpClient);
  baseUrl = "http://localhost:4999/api/";

  // getMergedChain(): Observable<Chain> {
  //   return this.http.get<Chain>(this.baseUrl + 'nodes/merged-chain');
  // }
  getMergedChain(): Observable<Chain> {
    return this.http.get<Chain>(this.baseUrl + 'nodes/merged-chain');
  }

  downloadFile(transaction: any) {
    if (!transaction?.content) return;

    const byteCharacters = atob(transaction.content);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const blob = new Blob([byteArray]);

    const link = document.createElement('a');
    link.href = window.URL.createObjectURL(blob);
    link.download = transaction.fileName || 'document';
    link.click();
    window.URL.revokeObjectURL(link.href);
  }
}
