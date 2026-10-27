import 'package:flutter/material.dart';

import '../controllers/register_controller.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() =>
      _RegisterScreenState();
}

class _RegisterScreenState
    extends State<RegisterScreen> {
  final _name = TextEditingController();
  final _email = TextEditingController();
  final _password =
      TextEditingController();

  final RegisterController
      _controller =
      RegisterController();

  bool _loading = false;

  @override
  void dispose() {
    _name.dispose();
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar:
          AppBar(title: const Text("Register")),
      body: Padding(
        padding:
            const EdgeInsets.all(20),
        child: Column(
          children: [
            TextField(
              controller: _name,
              decoration:
                  const InputDecoration(
                labelText: "Full Name",
              ),
            ),
            const SizedBox(height: 15),
            TextField(
              controller: _email,
              decoration:
                  const InputDecoration(
                labelText: "Email",
              ),
            ),
            const SizedBox(height: 15),
            TextField(
              controller: _password,
              obscureText: true,
              decoration:
                  const InputDecoration(
                labelText: "Password",
              ),
            ),
            const SizedBox(height: 25),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _loading
                    ? null
                    : () async {
                        setState(() {
                          _loading = true;
                        });

                        await _controller
                            .register(
                          context: context,
                          fullName:
                              _name.text.trim(),
                          email: _email.text
                              .trim(),
                          password:
                              _password.text,
                          language: "en",
                        );

                        if (!mounted) {
                          return;
                        }

                        setState(() {
                          _loading = false;
                        });
                      },
                child: _loading
                    ? const CircularProgressIndicator()
                    : const Text(
                        "REGISTER",
                      ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}