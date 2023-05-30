odoo.define("payment_moneris_checkout.payment_form", function (require) {
  "use strict";

  const core = require("web.core");
  const ajax = require("web.ajax");

  const checkoutForm = require("payment.checkout_form");
  const manageForm = require("payment.manage_form");
  const Dialog = require("web.Dialog");

  const _t = core._t;

  var response_codes = {
    "001": "Success",
    "902": "3-D Secure failed on response",
    "2001": "Invalid ticket/ticket re-use",
  };

  const monerisCheckoutMixin = {
    /**
     * Return all relevant inline form inputs based on the payment method type of the acquirer.
     *
     * @private
     * @param {number} acquirerId - The id of the selected acquirer
     * @return {Object} - An object mapping the name of inline form inputs to their DOM element
     */
    _getInlineFormInputs: function (acquirerId) {
      return {
        acquirer_id: document.getElementById(`mon_acquirer_id`),
        acquirer_state: document.getElementById(`mon_acquirer_state`),
        store_id: document.getElementById(`store_id`),
        api_token: document.getElementById(`api_token`),
        order_id: document.getElementById(`order_id`),
        window_href: document.getElementById(`window_href`),
      };
    },

    /**
     * Return the credit card or bank data to pass to the Accept.dispatch request.
     *
     * @private
     * @param {number} acquirerId - The id of the selected acquirer
     * @return {Object} - Data to pass to the Accept.dispatch request
     */
    _getPaymentDetails: function (acquirerId) {
      const inputs = this._getInlineFormInputs(acquirerId);
      try {
        var acquirerForm = this.$(".moneris_form");
        var inputsForm = $("input", acquirerForm);
        var formData = this.getMonerisFormData(inputsForm);
      } catch (error) {
        //console.log("error ===>>>", error);
        var formData = this.getMonerisFormData(inputs);

      }
      return formData;
    },

    /**
     * Prepare the inline form of Moneris for direct payment.
     *
     * @override method from payment.payment_form_mixin
     * @private
     * @param {string} provider - The provider of the selected payment option's acquirer
     * @param {number} paymentOptionId - The id of the selected payment option
     * @param {string} flow - The online payment flow of the selected payment option
     * @return {Promise}
     */
    _prepareInlineForm: function (provider, paymentOptionId, flow) {
      //console.log("_prepareInlineForm");
      if (provider !== "monerischeckout") {
        return this._super(...arguments);
      }

      if (flow === "token") {
        return Promise.resolve(); // Don't show the form for tokens
      }

      this._setPaymentFlow("direct");

      let acceptJSUrl = "https://gateway.moneris.com/chkt/js/chkt_v1.00.js";
      return this._rpc({
        route: "/payment/monerischeckout/get_acquirer_info",
        params: {
          acquirer_id: paymentOptionId,
        },
      })
        .then((acquirerInfo) => {
          if (acquirerInfo.state !== "enabled") {
            acceptJSUrl = "https://gatewayt.moneris.com/chkt/js/chkt_v1.00.js";
          }
          this.authorizeInfo = acquirerInfo;
        })
        .then(() => {
          ajax.loadJS(acceptJSUrl);
        })
        .guardedCatch((error) => {
          error.event.preventDefault();
          this._displayError(
            _t("Server Error"),
            _t("An error occurred when displayed this payment form."),
            error.message.data.message
          );
        });
    },

    /**
     * Dispatch the secure data to Moneris Checkout.
     *
     * @override method from payment.payment_form_mixin
     * @private
     * @param {string} provider - The provider of the payment option's acquirer
     * @param {number} paymentOptionId - The id of the payment option handling the transaction
     * @param {string} flow - The online payment flow of the transaction
     * @return {Promise}
     */
    _processPayment: function (provider, paymentOptionId, flow) {
      if (provider !== "monerischeckout" || flow === "token") {
        return this._super(...arguments); // Tokens are handled by the generic flow
      }

      if (!this._validateFormInputs(paymentOptionId)) {
        this._enableButton(); // The submit button is disabled at this point, enable it
        return Promise.resolve();
      }

      // // Build the authentication and card data objects to be dispatched to Moneris Checkout
      // const secureData = {
      //   authData: {
      //       apiLoginID: this.authorizeInfo.login_id,
      //       clientKey: this.authorizeInfo.client_key,
      //   },
      //   ...this._getPaymentDetails(paymentOptionId),
      // };

      var ev = {};
      ev.txContext = this.txContext;
      // ev.transactionRoute = this.txContext.transactionRoute;
      var checked_radio = this.$('input[name="radio"]:checked');
      this._createMonerisToken(ev, checked_radio);
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Payment Request for Moneris Checkout
     *
     * @override method from payment.payment_form_mixin
     * @private
     * @param {string} provider - The provider of the acquirer
     * @param {number} acquirerId - The id of the acquirer handling the transaction
     * @param {object} processingValues - The processing values of the transaction
     * @return {Promise}
     */
    _processDirectPayment: function (provider, acquirerId, processingValues) {
      //console.log("provider ===>>>", provider);
      //console.log("acquirerId ===>>>", acquirerId);
      //console.log("processingValues ===>>>", processingValues);

      if (provider !== "monerischeckout") {
        return this._super(...arguments);
      }

      //======================================================================
      //==========PROCESS MONERIS PAYMENT=====================================
      //======================================================================
    },

    /**
     * Handle the response from Moneris Checkout and initiate the payment.
     *
     * @private
     * @param {number} acquirerId - The id of the selected acquirer
     * @param {object} response - The payment ticket returned by Moneris Checkout
     * @return {Promise}
     */
    _responseHandler: function (acquirerId, response) {
      if (response.response_code != "001") {
        let error = "";
        response.messages.message.forEach(
          (msg) => (error += `${msg.code}: ${msg.text}\n`)
        );
        this._displayError(
          _t("Server Error"),
          _t("We are not able to process your payment."),
          error
        );
        return Promise.resolve();
      }

      // Create the transaction and retrieve the processing values
      //console.log("--------------------");
      return this._rpc({
        route: this.txContext.transactionRoute,
        params: this._prepareTransactionRouteParams(
          "monerischeckout",
          acquirerId,
          "direct"
        ),
      })
        .then((processingValues) => {
          // Initiate the payment
          return this._rpc({
            route: "/payment/monerischeckout/payment",
            params: {
              reference: processingValues.reference,
              partner_id: processingValues.partner_id,
              opaque_data: response.opaqueData,
              access_token: processingValues.access_token,
            },
          }).then(() => (window.location = "/payment/status"));
        })
        .guardedCatch((error) => {
          error.event.preventDefault();
          this._displayError(
            _t("Server Error"),
            _t("We are not able to process your payment."),
            error.message.data.message
          );
        });
    },

    /**
     * Checks that all payment inputs adhere to the DOM validation constraints.
     *
     * @private
     * @param {number} acquirerId - The id of the selected acquirer
     * @return {boolean} - Whether all elements pass the validation constraints
     */
    _validateFormInputs: function (acquirerId) {
      //console.log("_validateFormInputs ===>>>");
      const inputs = Object.values(this._getInlineFormInputs(acquirerId));
      //console.log("inputs ===>>>", inputs);
      return inputs.every((element) => element.reportValidity());
    },

            /**
         * Prepare the params to send to the transaction route.
         *
         * For an acquirer to overwrite generic params or to add acquirer-specific ones, it must
         * override this method and return the extended transaction route params.
         *
         * @private
         * @param {string} provider - The provider of the selected payment option's acquirer
         * @param {number} paymentOptionId - The id of the selected payment option
         * @param {string} flow - The online payment flow of the selected payment option
         * @return {object} The transaction route params
         */
          _prepareMonericCheckoutTransactionRouteParams: function (provider, paymentOptionId, flow) {
              return {
                  'payment_option_id': paymentOptionId,
                  'reference_prefix': this.txContext.referencePrefix !== undefined
                      ? this.txContext.referencePrefix.toString() : null,
                  'amount': this.txContext.amount !== undefined
                      ? parseFloat(this.txContext.amount) : null,
                  'currency_id': this.txContext.currencyId
                      ? parseInt(this.txContext.currencyId) : null,
                  'partner_id': parseInt(this.txContext.partnerId),
                  'invoice_id': this.txContext.invoiceId
                      ? parseInt(this.txContext.invoiceId) : null,
                  'flow': flow,
                  'tokenization_requested': this.txContext.tokenizationRequested,
                  'landing_route': this.txContext.landingRoute,
                  'is_validation': this.txContext.isValidation,
                  'access_token': this.txContext.accessToken
                      ? this.txContext.accessToken : undefined,
                  'csrf_token': core.csrf_token,
              };
          },


    // Moneris Checkout Functions

    /**
     * called when clicking on pay now or add payment event.
     *
     * @private
     * @param {Event} ev
     * @param {DOMElement} checkedRadio
     * @param {Boolean} addPmEvent
     */
    _createMonerisToken: function (ev, checked_radio, addPmEvent) {
      //console.log("_createMonerisToken");
      this.txContext = ev.txContext;

      var acquirerForm = this.$(".moneris_form");
      var inputsForm = $("input", acquirerForm);
      var formData = this.getMonerisFormData(inputsForm);

      if (this.options.partnerId === undefined) {
        console.warn(
          "payment_form: unset partner_id when adding new token; things could go wrong"
        );
      }
      var checked_radio = this.$('input[name="o_payment_radio"]:checked');
      var acquirer_id = this.getMonerisAcquirerIdFromRadio(checked_radio);
      //console.log("acquirer_id ===>>>", acquirer_id);
      this.txContext.acquirerId = acquirer_id;

      function myPageLoad(data) {
        //console.log("myPageLoad::data ==>>>", data);
        data = JSON.parse(data);
        if (data.handler == "page_loaded") {
          if (data.response_code == "001") {
            var chktLoading = document.getElementsByClassName("chkt_loading");
            if (chktLoading.length > 0) {
              chktLoading[0].style.display = "none";
            }
            var btnCheckout = document.getElementById("process");
            if (btnCheckout) {
              btnCheckout.style.display = "none";
            }
          } else {
            //console.log("myPageLoad failure--->", data.response_code);
            if (data.ticket) {
              myCheckout.closeCheckout([data.ticket]);
            }
            var monerisBtnCncl = document.getElementById("monerisBtnCncl");
            if (monerisBtnCncl) {
              monerisBtnCncl.click();
            }
            var message = "";
            if (data.response_code) {
              message = response_codes[data.response_code];
            }

            new Dialog(this, {
              title: _t("Moneris Checkout Error!"),
              size: "medium",
              $content: $("<div>").append(
                "Error Message: " +
                  message +
                  "\n.Please check your Moneris Checkout Configurations."
              ),
              buttons: [
                {
                  text: _t("Ok"),
                  classes: "btn-primary",
                  close: true,
                  click: execute,
                },
                {
                  text: _t("Cancel"),
                  close: true,
                },
              ],
            }).open();

          }
        }
      }

      function myErrorEvent(data) {
        //console.log("myErrorEvent::data ==>>>", data);
        // When an error occurs during the checkout process. This requires the Moneris Checkout
        // session to be closed using the closeCheckout function
        myCheckout.closeCheckout([data.ticket]);
      }

      function myCancelTransaction(data) {
        //console.log("myCancelTransaction::data ==>>>", data);
        myCheckout.closeCheckout([data.ticket]);
        var btnPay = document.getElementById("o_payment_form_pay");
        btnPay.disabled = false;
      }

      function myPaymentReceipt(data) {
        //console.log("myPaymentReceipt:data--->", data);

        var response = JSON.parse(data);
        //console.log("response--->", response);

        if (response.response_code == "001") {
          formData.ticket_no = response.ticket;
          var checked_radio = $('input[name="o_payment_radio"]:checked');
          //console.log("checked_radio--->", checked_radio);

          if (checked_radio.length > 0) {
            var acquirer = checked_radio[0];

            if (window.location.href.indexOf("shop/payment") > -1) {
              for (let index = 0; index < checked_radio.length; index++) {
                const element = checked_radio[index];
                if (element.dataset.provider == "monerischeckout") {
                  acquirer = checked_radio[index];
                }
              }
            }

            //console.log("acquirer--->", acquirer);
            //console.log("provider--->", acquirer.dataset.provider);

            if (acquirer.dataset.provider == "monerischeckout") {
              var acquirer_id = acquirer.dataset.acquirerID;
              //console.log("acquirer_id--->", acquirer_id);

              if (typeof data == "string") {
                data = JSON.parse(data);
              }

              if (data.ticket || data.name) {
                var ticket = data.name || data.ticket;
                //console.log("ticket--->", ticket);
                data.ticket = ticket;
                var request = {
                  acquirer_id: acquirer.dataset.acquirerID,
                  provider: acquirer.dataset.provider,
                  preload_response: data,
                  formData: formData,
                };
                //console.log("request--->", request);

                self
                  ._rpc({
                    route: "/payment/monerischeckout/receipt",
                    params: request,
                  })
                  .then(function (receipt) {
                    //console.log("receipt response", receipt);
                    if (receipt) {
                      if (receipt.response.success != "true") {
                        let error = "";
                        response.messages.message.forEach(
                          (msg) => (error += `${msg.code}: ${msg.text}\n`)
                        );
                        self._displayError(
                          _t("Server Error"),
                          _t("We are not able to process your payment."),
                          error
                        );
                        return Promise.resolve();
                      }

                      if (window.location.href.indexOf("asda") > -1) {
                        location.reload();
                      }else{
                         //debugger
                        var acquirerId = self.txContext.acquirerId;
                        var params = self._prepareMonericCheckoutTransactionRouteParams('monerischeckout', acquirerId, 'direct');

                        //console.log("acquirerId", self.txContext.acquirerId);
                        //console.log("transactionRoute", self.txContext.transactionRoute);
                        //console.log("params", params);
                        // Create the transaction and retrieve the processing values

                        return self._rpc({
                            route: self.txContext.transactionRoute,
                            params: self._prepareMonericCheckoutTransactionRouteParams('monerischeckout', acquirerId, 'direct'),
                        }).then(processingValues => {
                            //console.log("processingValues", processingValues);
                            // Initiate the payment
                            return self._rpc({
                                route: '/payment/monerischeckout/payment',
                                params: {
                                  // 'reference': receipt.response.request.order_no,
                                  // 'partner_id': receipt.response.request.cust_id.split("/")[1],
                                  'opaque_data': receipt,
                                  // 'access_token': receipt.formData.access_token,
                                  // 'csrf_token': receipt.formData.csrf_token,

                                  'reference': processingValues.reference,
                                  'partner_id': processingValues.partner_id,
                                  // 'opaque_data': response.opaqueData,
                                  'access_token': processingValues.access_token,
                                }
                            }).then(() => window.location = '/payment/status');
                        }).guardedCatch((error) => {
                            error.event.preventDefault();
                            self._displayError(
                                _t("Server Error"),
                                _t("We are not able to process your payment."),
                                error.message.data.message
                            );
                        });


                      }




                    } else {
                      var monerisBtnCncl =
                        document.getElementById("monerisBtnCncl");
                      if (monerisBtnCncl) {
                        monerisBtnCncl.click();
                      }
                      try {
                        myCheckout.closeCheckout([data.ticket]);
                        $("#monerisModal").modal("hide");
                      } catch (error) {}
                    }
                  })
                  .guardedCatch(function (error) {
                    error.event.preventDefault();
                    acquirerForm.removeClass("d-none");
                    alert("Server Error:We are not able to add your payment method at the moment.")
                    self._displayError(
                      _t("Server Error"),
                      _t(
                        "We are not able to add your payment method at the moment."
                      )
                    );
                  });


              }
            }
          }


        }

        myCheckout.closeCheckout([data.ticket]);
      }

      function myErrorEvent(data) {
        //console.log("myErrorEvent::data ==>>>", data);
        // When an error occurs during the checkout process. This requires the Moneris Checkout
        // session to be closed using the closeCheckout function
        myCheckout.closeCheckout([data.ticket]);
      }

      function myPaymentComplete(data) {
         //debugger
        var self = this;
        self.myPaymentReceipt(data);
      }

      function myPageClosed(data) {
        if (data.handler == "page_closed") {
          if (data.response_code == "001") {
            console.error(
              "User has closed window or clicked Browser back button or Reload Button"
            );
          } else if (data.ticket) {
            console.error("JavaScript error occurred from Moneris Script");
          }
        }
      }

      function myPaymentSubmitted(data) {
        if (data.handler == "payment_submitted") {
          if (data.response_code == "001") {
            msg =
              "Cardholder clicked Checkout button and payment processing is started.";
            //console.log(msg);
          }
        }
      }

      //======================================================================
      if (checked_radio) {
        if (checked_radio[0].dataset.provider == "monerischeckout") {
          if (
            window.location.href.includes("/shop/payment") ||
            window.location.href.includes("my/orders") ||
            window.location.href.includes("/my/invoices/") ||
            window.location.href.includes("/my/payment_method") ||
            window.location.href.includes("/website_payment")
          ) {
            //console.log("monerischeckout ===>>>>", checked_radio[0].dataset.provider)
             //debugger
            var myCheckout = new monerisCheckout();
            var self = this;

            //console.log("Create  myCheckout==>>>");
            // console.log(
            //   "  formData.acquirer_state==>>>",
            //   formData.acquirer_state
            // );

            if (formData.acquirer_state === "test") {
              myCheckout.setMode("qa");
            } else {
              myCheckout.setMode("prod");
            }
            myCheckout.setCheckoutDiv("monerisCheckout");
            myCheckout.setCallback("page_loaded", myPageLoad);
            myCheckout.setCallback("cancel_transaction", myCancelTransaction);
            myCheckout.setCallback("error_event", myErrorEvent);
            myCheckout.setCallback("payment_receipt", myPaymentReceipt);
            myCheckout.setCallback("payment_complete", myPaymentComplete);
            myCheckout.setCallback("page_closed", myPageClosed);
            myCheckout.setCallback("payment_submitted", myPaymentSubmitted);

            var session = session;
            var data = formData;
            data.acquirer_id = acquirer_id;
            data.href = window.location.href;

            if (window.location.href.includes("my/orders")) {
              data.sale_order_id = window.location.href
                .split("my/orders")[1]
                .split("/")[1]
                .split("?")[0];
            }

            if (window.location.href.includes("/my/invoices/")) {
              var invoice_id = window.location.href
                .split("/my/invoices/")[1]
                .split("?")[0];
              data.invoice_id = invoice_id;
            }
            try {
              var self = this;
              ajax
                  .jsonRpc("/payment/monerischeckout/preload", "call", data)
                  .then(function (result) {
                     //debugger
                    var result = JSON.parse(result);
                    //console.log("result", result);
                    let response_error = result.errors_message || result.errors
                    if (response_error){
                        throw (response_error)
                    }
                    if (result.response.ticket) {
                      var ticket = result.response.ticket;
                      self._enableButton();

                      //console.log("remove class[d-none]");
                      $.unblockUI();

                      const $submitButton = $('button[name="o_payment_submit_button"]');
                      $submitButton.removeClass("d-none");
                      var chktLoading = document.getElementsByClassName("monerisBody");
                      if (chktLoading.length > 0) {
                        chktLoading[0].style.display = "none";
                      }
                      myCheckout.startCheckout([ticket]);
                    }

                    if (result.response.ticket) {
                      if (
                          window.location.href.includes("/shop/payment") ||
                          window.location.href.includes("/my/payment_method") ||
                          window.location.href.includes("/my/orders") ||
                          window.location.href.includes("my/invoices") ||
                          window.location.href.includes("pay/invoices")
                      ) {
                        $("#monerisModal").modal('show');
                      }
                    }

                    if (result.response.success == "false") {
                      try {
                        //console.log("payment_method", window.location.href.includes("/my/payment_method"));
                        if (window.location.href.includes("/my/payment_method")) {
                        } else {
                          var monerisBtnCncl = document.getElementById("monerisBtnCncl");
                          if (monerisBtnCncl) {
                            // monerisBtnCncl.click();
                          }
                        }

                        //console.log("**********ENDS**************");


                      } catch (error) {
                      }

                      if (result.response.error) {
                        // alert(_t(JSON.stringify(result.response.error)));
                        // if (document.getElementsByName("o_payment_submit_button")) {
                        //   // document.getElementsByName("o_payment_submit_button")[0].removeClass("o_loader");
                        //   // document.getElementsByName("o_payment_submit_button")[0].disabled = "false";
                        //   self._enableButton();
                        self._displayError(
                        _t("Server Error"),
                        _t("An error occurred when displayed this payment form."),
                            _t(JSON.stringify(result.response.error))
                    );
                        // }
                      }
                    }

                  }).guardedCatch(function(error) {
                     //debugger
                    self._displayError(
                        _t("Server Error"),
                        _t("An error occurred when displayed this payment form ."),
                        _t(error)
                    );
                });;
            }
            catch (e) {
               //debugger
               self._displayError(
                        _t("Server Error"),
                        _t("An error occurred when displayed this payment form."),
                        _t(e)
                    );
            }
          }
        }
      }else{
        //console.log("Not Moneris Checkout")
      }
    },

    /**
     * @private
     * @param {DOMElement} element
     */
    getMonerisAcquirerIdFromRadio: function (element) {
      return $(element).data("paymentOptionId");
    },

    payMonerisEvent: function (ev) {
      //console.log("payMonerisEvent");
      ev.preventDefault();
      var checked_radio = this.$('input[name="o_payment_radio"]:checked');

      if (
        checked_radio.length === 1 &&
        this.isNewPaymentRadio(checked_radio) &&
        checked_radio.data("provider") === "monerischeckout"
      ) {
        if (window.location.href.includes("/my/invoices/")) {
          var pay_with = document.getElementById("pay_with");
          if (pay_with != undefined) {
            pay_with.style.display = "none";
          }
        }
        // if (window.location.href.includes("/my/orders/")) {
        //   var modalaccept = document.getElementById("modalaccept");
        //   if (modalaccept != undefined) {
        //     modalaccept.style.display = "none";
        //   }
        //   var modalaccept = document.getElementById("modalaccept");
        // }

        if (window.location.href.includes("/website_payment")) {
          var modalaccept = document.getElementById("modalaccept");
          if (modalaccept != undefined) {
            modalaccept.style.display = "none";
          }
          var modalaccept = document.getElementById("modalaccept");
        }

        var btnPay = document.getElementById("o_payment_form_pay");
        btnPay.dataset.toggle = "modal";
        btnPay.dataset.target = "#monerisModal";
        $("#monerisModal").modal({ backdrop: "static", keyboard: false });

        this._createMonerisToken(ev, checked_radio);
      } else {
        this._super.apply(this, arguments);
      }
    },

    /**
     * @private
     * @param {jQuery} $form
     */
    getMonerisFormData: function ($form) {
      var unindexed_array = $form.serializeArray();
      var indexed_array = {};

      $.map(unindexed_array, function (n, i) {
        indexed_array[n.name] = n.value;
      });
      return indexed_array;
    },
  };

  checkoutForm.include(monerisCheckoutMixin);
  manageForm.include(monerisCheckoutMixin);
});

  function monerisCancel() {
     //debugger
    // var btnPay = document.getElementById("o_payment_form_pay");
    // if (window.location.href.includes('/my/payment_method')) {} else {
    //     btnPay.disabled = false;
    // }

    try {
        $('.modal-backdrop').remove();
        myCheckout.closeCheckout()
    } catch (error) {}

}