#!/usr/bin/env sh
flask postgres initschema
flask install admin
flask install masterdata