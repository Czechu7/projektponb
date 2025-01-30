import { HttpClient } from '@angular/common/http';
import { HubConnection, HubConnectionBuilder } from '@microsoft/signalr';
import { inject, Injectable, signal } from '@angular/core';
import { User } from '../_models/user';
import { Observable } from 'rxjs/internal/Observable';
import { BehaviorSubject } from 'rxjs';
import { NodeStatus } from '../_models/nodeStatus';
import { Chain } from '../_models/chain';

@Injectable({
  providedIn: 'root'
})
export class DocumentsService {
  private http = inject(HttpClient);
  baseUrl = "http://localhost:4999/api/";
  
  getMergedChain(): Observable<Chain> {
    return this.http.get<Chain>(this.baseUrl + 'nodes/merged-chain');
  }
}
