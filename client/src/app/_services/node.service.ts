import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { User } from '../_models/user';
import { map } from 'rxjs';
import { Products } from '../_models/products';
import { Cart } from '../_models/cart';

@Injectable({
  providedIn: 'root'
})
export class NodeService {
  private http = inject(HttpClient);
  baseUrl = "http://localhost:4999/api/";


  disableNode(model: any){
    return this.http.post<any>(this.baseUrl + "nodes/disableNode", model).pipe(
        map(user =>{
            console.log("user", user);
        })
      )
  }

  corruptHash(model: any){
    return this.http.post<any>(this.baseUrl + "nodes/corruptHash", model).pipe(
        map(user =>{
            console.log("user", user);
        })
      )
  }

  corruptFile(model: any){
    return this.http.post<any>(this.baseUrl + "nodes/corruptFile", model).pipe(
        map(user =>{
            console.log("user", user);
        })
      )
  }
  corruptFileFix(model: any){
    return this.http.post<any>(this.baseUrl + "nodes/corruptFileFix", model).pipe(
        map(user =>{
            console.log("user", user);
        })
      )
  }
}
