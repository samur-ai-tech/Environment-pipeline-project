// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "EditorSubsystem.h"
#include "Interfaces/IHttpRequest.h"
#include "WorldBLDAuthSubsystem.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnAuthSuccess, const FString&, SessionToken);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnAuthError, const FString&, ErrorMessage);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnAuthTarget2FA);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnSessionValid);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnSessionInvalid);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnEmailCheckSuccess);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnEmailCheckFailure, const FString&, ErrorMessage);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnLicensesUpdated, const TArray<FString>&, AuthorizedTools);

// Native (non-UObject) delegates for Slate/C++ callers that shouldn't rely on dynamic delegate plumbing.
DECLARE_MULTICAST_DELEGATE_OneParam(FOnAuthSuccessNative, const FString& /*SessionToken*/);
DECLARE_MULTICAST_DELEGATE_OneParam(FOnAuthErrorNative, const FString& /*ErrorMessage*/);
DECLARE_MULTICAST_DELEGATE(FOnAuthTarget2FANative);

/**
 * Subsystem to handle authentication with WorldBLD backend.
 */
UCLASS()
class WORLDBLDEDITOR_API UWorldBLDAuthSubsystem : public UEditorSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	/**
	 * Log in with email and password.
	 * @param Email User email
	 * @param Password User password
	 * @param OTP Optional One-Time Password for 2FA
	 */
	UFUNCTION(BlueprintCallable, Category = "WorldBLD|Auth")
	void Login(const FString& Email, const FString& Password, const FString& OTP = TEXT(""));

	/**
	 * Check if an account exists for the provided email by calling the login endpoint
	 * with an empty password and interpreting the backend error codes.
	 */
	UFUNCTION(BlueprintCallable, Category = "WorldBLD|Auth")
	void CheckEmail(const FString& Email);

	/**
	 * Log out and clear stored session.
	 */
	UFUNCTION(BlueprintCallable, Category = "WorldBLD|Auth")
	void Logout();

	/**
	 * Check if currently logged in (Offline check).
	 * Checks if a session token exists in the local config.
	 */
	UFUNCTION(BlueprintCallable, Category = "WorldBLD|Auth")
	static bool IsLoggedIn();

	/**
	 * Validate the current session with the server (Online check).
	 * Fires OnSessionValid or OnSessionInvalid.
	 */
	UFUNCTION(BlueprintCallable, Category = "WorldBLD|Auth")
	void ValidateSession();

	/**
	 * Get the current session token.
	 */
	UFUNCTION(BlueprintCallable, Category = "WorldBLD|Auth")
	FString GetSessionToken() const;

	/**
	 * Get the cached user credits (0 if unknown).
	 * Cached from session validation and/or updated after a successful purchase.
	 */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "WorldBLD|Auth")
	int32 GetUserCredits() const;

	/** Set cached user credits (clamped to >= 0). */
	void SetCachedUserCredits(int32 InCredits);

	/**
	 * Get the cached user name.
	 * Cached from session validation.
	 */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "WorldBLD|Auth")
	FString GetUserName() const;

	/**
	 * Stable, unique identifier for the signed-in account, or EMPTY when it is not yet known.
	 *
	 * Unlike GetUserName(), this never substitutes a display placeholder and is never a display
	 * name, so it is safe to use as an identity key. Callers must treat an empty result as
	 * "identity unknown, retry later" rather than as an account in its own right - guessing an
	 * identity here lets one account's entitlements apply to another.
	 *
	 * Populated from session validation, so it is empty for a short window at editor startup.
	 */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "WorldBLD|Auth")
	FString GetAccountId() const;

	/**
	 * Fetches the signed-in account's stable id when it is not cached yet.
	 *
	 * Unlike ValidateSession(), this has no side effects beyond caching the id: it never logs out,
	 * never broadcasts OnSessionValid/OnSessionInvalid, and leaves the user name and credits alone.
	 * Single-flight and throttled, so it is safe to call from per-action code.
	 */
	void RefreshAccountIdentity();

	/**
	 * Check if the user has a license for the specified tool.
	 * Returns true if ToolId is contained within any of the authorized tool strings.
	 * @param ToolId The tool identifier to check (e.g., "CityBLD", "RoadBLD")
	 */
	UFUNCTION(BlueprintCallable, Category = "WorldBLD|License")
	bool HasLicenseForTool(const FString& ToolId) const;

	/**
	 * Get the list of all authorized tools for the current user.
	 */
	UFUNCTION(BlueprintCallable, Category = "WorldBLD|License")
	TArray<FString> GetAuthorizedTools() const;

	/**
	 * Manually trigger a license refresh from the server.
	 */
	UFUNCTION(BlueprintCallable, Category = "WorldBLD|License")
	void RefreshLicenses();

public:
	UPROPERTY(BlueprintAssignable, Category = "WorldBLD|Auth")
	FOnAuthSuccess OnLoginSuccess;

	UPROPERTY(BlueprintAssignable, Category = "WorldBLD|Auth")
	FOnAuthError OnLoginFail;

	UPROPERTY(BlueprintAssignable, Category = "WorldBLD|Auth")
	FOnAuthTarget2FA OnTwoFactorRequired;

	// Native events (preferred for Slate / pure C++).
	FOnAuthSuccessNative OnLoginSuccessNative;
	FOnAuthErrorNative OnLoginFailNative;
	FOnAuthTarget2FANative OnTwoFactorRequiredNative;

	UPROPERTY(BlueprintAssignable, Category = "WorldBLD|Auth")
	FOnSessionValid OnSessionValid;

	UPROPERTY(BlueprintAssignable, Category = "WorldBLD|Auth")
	FOnSessionInvalid OnSessionInvalid;

	UPROPERTY(BlueprintAssignable, Category = "WorldBLD|Auth")
	FOnEmailCheckSuccess OnEmailCheckSuccess;

	UPROPERTY(BlueprintAssignable, Category = "WorldBLD|Auth")
	FOnEmailCheckFailure OnEmailCheckFailure;

	/** Called whenever the authorized tools list is updated from the server */
	UPROPERTY(BlueprintAssignable, Category = "WorldBLD|License")
	FOnLicensesUpdated OnLicensesUpdated;

private:
	void OnLoginResponseReceived(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bConnectedSuccessfully);
	void OnCheckEmailResponseReceived(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bConnectedSuccessfully);
	void OnLoginSessionValidationReceived(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bConnectedSuccessfully);
	void OnSessionValidationReceived(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bConnectedSuccessfully);
	void OnLicensesResponseReceived(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bConnectedSuccessfully);

	void SetSessionToken(const FString& Token);
	void LoadSessionToken();

	/** Start polling for license updates (called after login) */
	void StartLicensePolling();

	/** Stop polling for license updates (called on logout) */
	void StopLicensePolling();

	/** Timer callback for license polling */
	void OnLicensePollingTick();

	/** Caches the stable account identity from a session response's "user" object. */
	void CacheAccountIdFromUserObject(const TSharedPtr<class FJsonObject>& UserObject);

	FString CurrentSessionToken;
	FString PendingLoginSessionToken;
	FString CachedEmail;
	FString CachedPassword; // Cached temporarily solely for 2FA retry flow if needed

	/** Array of authorized tool strings from the server */
	TArray<FString> AuthorizedTools;

	/** Timer handle for license polling */
	FTimerHandle LicensePollingTimerHandle;

	/** Polling interval in seconds */
	static constexpr float LicensePollingInterval = 15.0f;

	/** Cached credits parsed from GET /api/auth/desktop/session (or set after a purchase completes). */
	int32 CachedUserCredits = 0;
	bool bHasCachedUserCredits = false;

	/** Cached user name from session validation */
	FString CachedUserName;

	/**
	 * Stable account identity from session validation (user._id, falling back to user.email).
	 *
	 * Distinct from CachedEmail, which holds the login form's address only for the duration of the
	 * login/2FA flow and is deliberately cleared afterwards. Empty until session validation lands.
	 */
	FString CachedAccountId;

	// Appended after every pre-existing member on purpose: tool binaries built against an older
	// WorldBLD must keep seeing the same offsets for the members that existed then.

	/** FPlatformTime::Seconds() of the last RefreshAccountIdentity request; 0 when none has been sent. */
	double LastAccountIdentityRequestSeconds = 0.0;

	/** True while a RefreshAccountIdentity request is outstanding. */
	bool bAccountIdentityRequestInFlight = false;
};
