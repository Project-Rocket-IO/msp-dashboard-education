// Stripe Checkout Handler
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Stripe
    let stripe;
    
    // Get Stripe public key
    fetch('/payments/config/')
        .then(response => response.json())
        .then(data => {
            stripe = Stripe(data.publicKey);
        })
        .catch(error => {
            console.error('Error loading Stripe config:', error);
        });

    // Basic Package Checkout
    document.getElementById('submitBtnbasic').addEventListener('click', function() {
        if (!stripe) {
            console.error('Stripe not initialized');
            return;
        }
        
        // Show loading state
        this.disabled = true;
        this.innerHTML = '<i class="ri-loader-4-line align-middle me-2"></i>Loading...';
        
        fetch('/payments/basic-checkout-session/')
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error('Error:', data.error);
                    alert('Error creating checkout session: ' + data.error);
                    // Reset button
                    this.disabled = false;
                    this.innerHTML = '<i class="ri-vip-crown-fill align-middle me-2"></i>Purchase Subscription';
                } else {
                    return stripe.redirectToCheckout({
                        sessionId: data.sessionId
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error creating checkout session');
                // Reset button
                this.disabled = false;
                this.innerHTML = '<i class="ri-vip-crown-fill align-middle me-2"></i>Purchase Subscription';
            });
    });

    // Premium Package Checkout
    document.getElementById('submitBtnpremium').addEventListener('click', function() {
        if (!stripe) {
            console.error('Stripe not initialized');
            return;
        }
        
        // Show loading state
        this.disabled = true;
        this.innerHTML = '<i class="ri-loader-4-line align-middle me-2"></i>Loading...';
        
        fetch('/payments/premium-checkout-session/')
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error('Error:', data.error);
                    alert('Error creating checkout session: ' + data.error);
                    // Reset button
                    this.disabled = false;
                    this.innerHTML = '<i class="ri-vip-crown-fill align-middle me-2"></i>Purchase Subscription';
                } else {
                    return stripe.redirectToCheckout({
                        sessionId: data.sessionId
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error creating checkout session');
                // Reset button
                this.disabled = false;
                this.innerHTML = '<i class="ri-vip-crown-fill align-middle me-2"></i>Purchase Subscription';
            });
    });

    // All Inclusive Package Checkout
    document.getElementById('submitBtnallinc').addEventListener('click', function() {
        if (!stripe) {
            console.error('Stripe not initialized');
            return;
        }
        
        // Show loading state
        this.disabled = true;
        this.innerHTML = '<i class="ri-loader-4-line align-middle me-2"></i>Loading...';
        
        fetch('/payments/allinc-checkout-session/')
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error('Error:', data.error);
                    alert('Error creating checkout session: ' + data.error);
                    // Reset button
                    this.disabled = false;
                    this.innerHTML = '<i class="ri-vip-crown-fill align-middle me-2"></i>Purchase Subscription';
                } else {
                    return stripe.redirectToCheckout({
                        sessionId: data.sessionId
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error creating checkout session');
                // Reset button
                this.disabled = false;
                this.innerHTML = '<i class="ri-vip-crown-fill align-middle me-2"></i>Purchase Subscription';
            });
    });
}); 