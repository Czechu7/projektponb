import { Component, inject } from '@angular/core';
import { AccountService } from '../../_services/account.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-cart',
  standalone: true,
  imports: [],
  templateUrl: './cart.component.html',
  styleUrl: './cart.component.css'
})
export class CartComponent {
  accountService = inject(AccountService)
  router = inject(Router);
  cart: any;

  ngOnInit() {
    this.accountService.getCart().subscribe({
      next: cart => this.cart = cart,
      error: error => console.log(error),
      complete: () => console.log('Request has been completed')
    });
  }

  addCart() {
    this.accountService.addCart(this.cart).subscribe({
      next: cart => this.cart = cart,
      error: error => console.log(error),
      complete: () => console.log('Request has been completed')
    });
  }

  
  navigateToCart(id: number) {
    this.router.navigate(['/cart', id]);
  }
}